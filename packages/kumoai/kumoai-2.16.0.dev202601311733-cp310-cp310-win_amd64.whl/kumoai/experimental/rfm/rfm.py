import copy
import json
import math
import time
import warnings
from collections import defaultdict
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Any, Literal, overload

import pandas as pd
from kumoapi.model_plan import RunMode
from kumoapi.pquery import QueryType, ValidatedPredictiveQuery
from kumoapi.pquery.AST import (
    Aggregation,
    Column,
    Condition,
    Join,
    LogicalOperation,
)
from kumoapi.rfm import Context
from kumoapi.rfm import Explanation as ExplanationConfig
from kumoapi.rfm import (
    RFMEvaluateRequest,
    RFMParseQueryRequest,
    RFMPredictRequest,
)
from kumoapi.task import TaskType
from kumoapi.typing import AggregationType, Stype
from rich.console import Console
from rich.markdown import Markdown

from kumoai import in_notebook
from kumoai.client.rfm import RFMAPI
from kumoai.exceptions import HTTPException
from kumoai.experimental.rfm import Graph, TaskTable
from kumoai.experimental.rfm.base import DataBackend, Sampler
from kumoai.mixin import CastMixin
from kumoai.utils import ProgressLogger, display

_RANDOM_SEED = 42

_MAX_PRED_SIZE: dict[TaskType, int] = defaultdict(lambda: 1_000)
_MAX_PRED_SIZE[TaskType.TEMPORAL_LINK_PREDICTION] = 200

_MAX_TEST_SIZE: dict[TaskType, int] = defaultdict(lambda: 2_000)
_MAX_TEST_SIZE[TaskType.TEMPORAL_LINK_PREDICTION] = 400

_MAX_CONTEXT_SIZE = {
    RunMode.DEBUG: 100,
    RunMode.FAST: 1_000,
    RunMode.NORMAL: 5_000,
    RunMode.BEST: 10_000,
}

_DEFAULT_NUM_NEIGHBORS = {
    RunMode.DEBUG: [16, 16, 4, 4, 1, 1],
    RunMode.FAST: [32, 32, 8, 8, 4, 4],
    RunMode.NORMAL: [64, 64, 8, 8, 4, 4],
    RunMode.BEST: [64, 64, 8, 8, 4, 4],
}

_MAX_SIZE = 30 * 1024 * 1024
_SIZE_LIMIT_MSG = ("Context size exceeds the 30MB limit. {stats}\nPlease "
                   "reduce either the number of tables in the graph, their "
                   "number of columns (e.g., large text columns), "
                   "neighborhood configuration, or the run mode. If none of "
                   "this is possible, please create a feature request at "
                   "'https://github.com/kumo-ai/kumo-rfm' if you must go "
                   "beyond this for your use-case.")


@dataclass(repr=False)
class ExplainConfig(CastMixin):
    """Configuration for explainability.

    Args:
        skip_summary: Whether to skip generating a human-readable summary of
            the explanation.
    """
    skip_summary: bool = False


@dataclass(repr=False)
class Explanation:
    prediction: pd.DataFrame
    summary: str
    details: ExplanationConfig

    @overload
    def __getitem__(self, index: Literal[0]) -> pd.DataFrame:
        pass

    @overload
    def __getitem__(self, index: Literal[1]) -> str:
        pass

    def __getitem__(self, index: int) -> pd.DataFrame | str:
        if index == 0:
            return self.prediction
        if index == 1:
            return self.summary
        raise IndexError("Index out of range")

    def __iter__(self) -> Iterator[pd.DataFrame | str]:
        return iter((self.prediction, self.summary))

    def __repr__(self) -> str:
        return str((self.prediction, self.summary))

    def __str__(self) -> str:
        console = Console(soft_wrap=True)
        with console.capture() as cap:
            console.print(display.to_rich_table(self.prediction))
            console.print(Markdown(self.summary))
        return cap.get()[:-1]

    def print(self) -> None:
        r"""Prints the explanation."""
        if in_notebook():
            display.dataframe(self.prediction)
            display.message(self.summary)
        else:
            print(self)

    def _ipython_display_(self) -> None:
        self.print()


class KumoRFM:
    r"""The Kumo Relational Foundation model (RFM) from the `KumoRFM: A
    Foundation Model for In-Context Learning on Relational Data
    <https://kumo.ai/research/kumo_relational_foundation_model.pdf>`_ paper.

    :class:`KumoRFM` is a foundation model to generate predictions for any
    relational dataset without training.
    The model is pre-trained and the class provides an interface to query the
    model from a :class:`Graph` object.

    .. code-block:: python

        from kumoai.experimental.rfm import Graph, KumoRFM

        df_users = pd.DataFrame(...)
        df_items = pd.DataFrame(...)
        df_orders = pd.DataFrame(...)

        graph = Graph.from_data({
            'users': df_users,
            'items': df_items,
            'orders': df_orders,
        })

        rfm = KumoRFM(graph)

        query = ("PREDICT COUNT(orders.*, 0, 30, days)>0 "
                 "FOR users.user_id=1")
        result = rfm.predict(query)

        print(result)  # user_id  COUNT(transactions.*, 0, 30, days) > 0
                       # 1        0.85

    Args:
        graph: The graph.
        verbose: Whether to print verbose output.
        optimize: If set to ``True``, will optimize the underlying data backend
            for optimal querying. For example, for transactional database
            backends, will create any missing indices. Requires write-access to
            the data backend.
    """
    def __init__(
        self,
        graph: Graph,
        verbose: bool | ProgressLogger = True,
        optimize: bool = False,
    ) -> None:
        graph = graph.validate()
        self._graph_def = graph._to_api_graph_definition()

        if graph.backend == DataBackend.LOCAL:
            from kumoai.experimental.rfm.backend.local import LocalSampler
            self._sampler: Sampler = LocalSampler(graph, verbose)
        elif graph.backend == DataBackend.SQLITE:
            from kumoai.experimental.rfm.backend.sqlite import SQLiteSampler
            self._sampler = SQLiteSampler(graph, verbose, optimize)
        elif graph.backend == DataBackend.SNOWFLAKE:
            from kumoai.experimental.rfm.backend.snow import SnowSampler
            self._sampler = SnowSampler(graph, verbose)
        else:
            raise NotImplementedError

        self._client: RFMAPI | None = None

        self._batch_size: int | Literal['max'] | None = None
        self._num_retries: int = 0

    @property
    def _api_client(self) -> RFMAPI:
        if self._client is not None:
            return self._client

        from kumoai.experimental.rfm import global_state
        self._client = RFMAPI(global_state.client)
        return self._client

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @contextmanager
    def retry(
        self,
        num_retries: int = 1,
    ) -> Generator[None, None, None]:
        """Context manager to retry failed queries due to unexpected server
        issues.

        .. code-block:: python

            with model.retry(num_retries=1):
                df = model.predict(query, indices=...)

        Args:
            num_retries: The maximum number of retries.
        """
        if num_retries < 0:
            raise ValueError(f"'num_retries' must be greater than or equal to "
                             f"zero (got {num_retries})")

        self._num_retries = num_retries
        yield
        self._num_retries = 0

    @contextmanager
    def batch_mode(
        self,
        batch_size: int | Literal['max'] = 'max',
        num_retries: int = 1,
    ) -> Generator[None, None, None]:
        """Context manager to predict in batches.

        .. code-block:: python

            with model.batch_mode(batch_size='max', num_retries=1):
                df = model.predict(query, indices=...)

        Args:
            batch_size: The batch size. If set to ``"max"``, will use the
                maximum applicable batch size for the given task.
            num_retries: The maximum number of retries for failed queries due
                to unexpected server issues.
        """
        if batch_size != 'max' and batch_size <= 0:
            raise ValueError(f"'batch_size' must be greater than zero "
                             f"(got {batch_size})")

        self._batch_size = batch_size
        with self.retry(self._num_retries or num_retries):
            yield
        self._batch_size = None

    @overload
    def predict(
        self,
        query: str | ValidatedPredictiveQuery,
        indices: Sequence[str] | Sequence[float] | Sequence[int] | None = None,
        *,
        explain: Literal[False] = False,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        verbose: bool | ProgressLogger = True,
        use_prediction_time: bool = False,
    ) -> pd.DataFrame:
        pass

    @overload
    def predict(
        self,
        query: str | ValidatedPredictiveQuery,
        indices: Sequence[str] | Sequence[float] | Sequence[int] | None = None,
        *,
        explain: Literal[True] | ExplainConfig | dict[str, Any],
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        verbose: bool | ProgressLogger = True,
        use_prediction_time: bool = False,
    ) -> Explanation:
        pass

    @overload
    def predict(
        self,
        query: str | ValidatedPredictiveQuery,
        indices: Sequence[str] | Sequence[float] | Sequence[int] | None = None,
        *,
        explain: bool | ExplainConfig | dict[str, Any] = False,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        verbose: bool | ProgressLogger = True,
        use_prediction_time: bool = False,
    ) -> pd.DataFrame | Explanation:
        pass

    def predict(
        self,
        query: str | ValidatedPredictiveQuery,
        indices: Sequence[str] | Sequence[float] | Sequence[int] | None = None,
        *,
        explain: bool | ExplainConfig | dict[str, Any] = False,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        verbose: bool | ProgressLogger = True,
        use_prediction_time: bool = False,
    ) -> pd.DataFrame | Explanation:
        """Returns predictions for a predictive query.

        Args:
            query: The predictive query.
            indices: The entity primary keys to predict for. Will override the
                indices given as part of the predictive query. Predictions will
                be generated for all indices, independent of whether they
                fulfill entity filter constraints.
            explain: Configuration for explainability.
                If set to ``True``, will additionally explain the prediction.
                Passing in an :class:`ExplainConfig` instance provides control
                over which parts of explanation are generated.
                Explainability is currently only supported for single entity
                predictions with ``run_mode="FAST"``.
            anchor_time: The anchor timestamp for the prediction. If set to
                ``None``, will use the maximum timestamp in the data.
                If set to ``"entity"``, will use the timestamp of the entity.
            context_anchor_time: The maximum anchor timestamp for context
                examples. If set to ``None``, ``anchor_time`` will
                determine the anchor time for context examples.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            max_pq_iterations: The maximum number of iterations to perform to
                collect valid labels. It is advised to increase the number of
                iterations in case the predictive query has strict entity
                filters, in which case, :class:`KumoRFM` needs to sample more
                entities to find valid labels.
            random_seed: A manual seed for generating pseudo-random numbers.
            verbose: Whether to print verbose output.
            use_prediction_time: Whether to use the anchor timestamp as an
                additional feature during prediction. This is typically
                beneficial for time series forecasting tasks.

        Returns:
            The predictions as a :class:`pandas.DataFrame`.
            If ``explain`` is provided, returns an :class:`Explanation` object
            containing the prediction, summary, and details.
        """
        query_def = self._parse_query(query)

        if indices is None:
            if query_def.rfm_entity_ids is None:
                raise ValueError("Cannot find entities to predict for. Please "
                                 "pass them via `predict(query, indices=...)`")
            indices = query_def.get_rfm_entity_id_list()
        query_def = replace(
            query_def,
            for_each='FOR EACH',
            rfm_entity_ids=None,
        )

        if not isinstance(verbose, ProgressLogger):
            query_repr = query_def.to_string(rich=True, exclude_predict=True)
            if explain is not False:
                msg = f'[bold]EXPLAIN[/bold] {query_repr}'
            else:
                msg = f'[bold]PREDICT[/bold] {query_repr}'
            verbose = ProgressLogger.default(msg=msg, verbose=verbose)

        with verbose as logger:
            task_table = self._get_task_table(
                query=query_def,
                indices=indices,
                anchor_time=anchor_time,
                context_anchor_time=context_anchor_time,
                run_mode=run_mode,
                max_pq_iterations=max_pq_iterations,
                random_seed=random_seed,
                logger=logger,
            )
            task_table._query = query_def.to_string()

            return self.predict_task(
                task_table,
                explain=explain,
                run_mode=run_mode,
                num_neighbors=num_neighbors,
                num_hops=num_hops,
                verbose=verbose,
                exclude_cols_dict=query_def.get_exclude_cols_dict(),
                use_prediction_time=use_prediction_time,
                top_k=query_def.top_k,
            )

    @overload
    def predict_task(
        self,
        task: TaskTable,
        *,
        explain: Literal[False] = False,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        verbose: bool | ProgressLogger = True,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        use_prediction_time: bool = False,
        top_k: int | None = None,
    ) -> pd.DataFrame:
        pass

    @overload
    def predict_task(
        self,
        task: TaskTable,
        *,
        explain: Literal[True] | ExplainConfig | dict[str, Any],
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        verbose: bool | ProgressLogger = True,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        use_prediction_time: bool = False,
        top_k: int | None = None,
    ) -> Explanation:
        pass

    @overload
    def predict_task(
        self,
        task: TaskTable,
        *,
        explain: bool | ExplainConfig | dict[str, Any] = False,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        verbose: bool | ProgressLogger = True,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        use_prediction_time: bool = False,
        top_k: int | None = None,
    ) -> pd.DataFrame | Explanation:
        pass

    def predict_task(
        self,
        task: TaskTable,
        *,
        explain: bool | ExplainConfig | dict[str, Any] = False,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        verbose: bool | ProgressLogger = True,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        use_prediction_time: bool = False,
        top_k: int | None = None,
    ) -> pd.DataFrame | Explanation:
        """Returns predictions for a custom task specification.

        Args:
            task: The custom :class:`TaskTable`.
            explain: Configuration for explainability.
                If set to ``True``, will additionally explain the prediction.
                Passing in an :class:`ExplainConfig` instance provides control
                over which parts of explanation are generated.
                Explainability is currently only supported for single entity
                predictions with ``run_mode="FAST"``.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            verbose: Whether to print verbose output.
            exclude_cols_dict: Any column in any table to exclude from the
                model input.
            use_prediction_time: Whether to use the anchor timestamp as an
                additional feature during prediction. This is typically
                beneficial for time series forecasting tasks.
            top_k: The number of predictions to return per entity.

        Returns:
            The predictions as a :class:`pandas.DataFrame`.
            If ``explain`` is provided, returns an :class:`Explanation` object
            containing the prediction, summary, and details.
        """
        if num_hops != 2 and num_neighbors is not None:
            warnings.warn(f"Received custom 'num_neighbors' option; ignoring "
                          f"custom 'num_hops={num_hops}' option")
        if num_neighbors is None:
            key = RunMode.FAST if task.task_type.is_link_pred else run_mode
            num_neighbors = _DEFAULT_NUM_NEIGHBORS[key][:num_hops]

        explain_config: ExplainConfig | None = None
        if explain is True:
            explain_config = ExplainConfig()
        elif explain is not False:
            explain_config = ExplainConfig._cast(explain)

        if explain_config is not None and run_mode in {
                RunMode.NORMAL, RunMode.BEST
        }:
            warnings.warn(f"Explainability is currently only supported for "
                          f"run mode 'FAST' (got '{run_mode}'). Provided run "
                          f"mode has been reset. Please lower the run mode to "
                          f"suppress this warning.")
            run_mode = RunMode.FAST

        if explain_config is not None and task.num_prediction_examples > 1:
            raise ValueError(f"Cannot explain predictions for more than a "
                             f"single entity "
                             f"(got {task.num_prediction_examples:,})")

        if not isinstance(verbose, ProgressLogger):
            if task.task_type == TaskType.BINARY_CLASSIFICATION:
                task_type_repr = 'binary classification'
            elif task.task_type == TaskType.MULTICLASS_CLASSIFICATION:
                task_type_repr = 'multi-class classification'
            elif task.task_type == TaskType.REGRESSION:
                task_type_repr = 'regression'
            elif task.task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                task_type_repr = 'link prediction'
            else:
                task_type_repr = str(task.task_type)

            if explain_config is not None:
                msg = f"Explaining {task_type_repr} task"
            else:
                msg = f"Predicting {task_type_repr} task"
            verbose = ProgressLogger.default(msg=msg, verbose=verbose)

        with verbose as logger:
            if task.num_context_examples > _MAX_CONTEXT_SIZE[run_mode]:
                logger.log(f"Sub-sampled {_MAX_CONTEXT_SIZE[run_mode]:,} "
                           f"out of {task.num_context_examples:,} in-context "
                           f"examples")
                task = task.narrow_context(0, _MAX_CONTEXT_SIZE[run_mode])

            if self._batch_size is None:
                batch_size = task.num_prediction_examples
            elif self._batch_size == 'max':
                batch_size = _MAX_PRED_SIZE[task.task_type]
            else:
                batch_size = self._batch_size

            if batch_size > _MAX_PRED_SIZE[task.task_type]:
                raise ValueError(f"Cannot predict for more than "
                                 f"{_MAX_PRED_SIZE[task.task_type]:,} "
                                 f"entities at once (got {batch_size:,}). Use "
                                 f"`KumoRFM.batch_mode` to process entities "
                                 f"in batches with a sufficient batch size.")

            if task.num_prediction_examples > batch_size:
                num = math.ceil(task.num_prediction_examples / batch_size)
                logger.log(f"Splitting {task.num_prediction_examples:,} "
                           f"entities into {num:,} batches of size "
                           f"{batch_size:,}")

            predictions: list[pd.DataFrame] = []
            summary: str | None = None
            details: Explanation | None = None
            for start in range(0, task.num_prediction_examples, batch_size):
                context = self._get_context(
                    task=task.narrow_prediction(start, length=batch_size),
                    run_mode=run_mode,
                    num_neighbors=num_neighbors,
                    exclude_cols_dict=exclude_cols_dict,
                    top_k=top_k,
                )
                context.y_test = None

                request = RFMPredictRequest(
                    context=context,
                    run_mode=RunMode(run_mode),
                    query=task._query,
                    use_prediction_time=use_prediction_time,
                )
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='gencode')
                    request_msg = request.to_protobuf()
                    _bytes = request_msg.SerializeToString()
                if start == 0:
                    logger.log(f"Generated context of size "
                               f"{len(_bytes) / (1024*1024):.2f}MB")

                if len(_bytes) > _MAX_SIZE:
                    stats = Context.get_memory_stats(request_msg.context)
                    raise ValueError(_SIZE_LIMIT_MSG.format(stats=stats))

                if start == 0 and task.num_prediction_examples > batch_size:
                    num = math.ceil(task.num_prediction_examples / batch_size)
                    verbose.init_progress(msg='Predicting', total=num)

                for attempt in range(self._num_retries + 1):
                    try:
                        if explain_config is not None:
                            resp = self._api_client.explain(
                                request=_bytes,
                                skip_summary=explain_config.skip_summary,
                            )
                            summary = resp.summary
                            details = resp.details
                        else:
                            resp = self._api_client.predict(_bytes)
                        df = pd.DataFrame(**resp.prediction)

                        # Cast 'ENTITY' to correct data type:
                        if 'ENTITY' in df:
                            table_dict = context.subgraph.table_dict
                            table = table_dict[context.entity_table_names[0]]
                            ser = table.df[table.primary_key]
                            df['ENTITY'] = df['ENTITY'].astype(ser.dtype)

                        # Cast 'ANCHOR_TIMESTAMP' to correct data type:
                        if 'ANCHOR_TIMESTAMP' in df:
                            ser = df['ANCHOR_TIMESTAMP']
                            if not pd.api.types.is_datetime64_any_dtype(ser):
                                if isinstance(ser.iloc[0], str):
                                    unit = None
                                else:
                                    unit = 'ms'
                                df['ANCHOR_TIMESTAMP'] = pd.to_datetime(
                                    ser, errors='coerce', unit=unit)

                        predictions.append(df.reset_index(drop=True))

                        if task.num_prediction_examples > batch_size:
                            verbose.step()

                        break
                    except HTTPException as e:
                        if attempt == self._num_retries:
                            try:
                                msg = json.loads(e.detail)['detail']
                            except Exception:
                                msg = e.detail
                            raise RuntimeError(
                                f"An unexpected exception occurred. Please "
                                f"create an issue at "
                                f"'https://github.com/kumo-ai/kumo-rfm'. {msg}"
                            ) from None

                        time.sleep(2**attempt)  # 1s, 2s, 4s, 8s, ...

        if len(predictions) == 1:
            prediction = predictions[0]
        else:
            prediction = pd.concat(predictions, ignore_index=True)

        if explain_config is not None:
            assert len(predictions) == 1
            assert summary is not None
            assert details is not None
            return Explanation(
                prediction=prediction,
                summary=summary,
                details=details,
            )

        return prediction

    def evaluate(
        self,
        query: str,
        *,
        metrics: list[str] | None = None,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        verbose: bool | ProgressLogger = True,
        use_prediction_time: bool = False,
    ) -> pd.DataFrame:
        """Evaluates a predictive query.

        Args:
            query: The predictive query.
            metrics: The metrics to use.
            anchor_time: The anchor timestamp for the prediction. If set to
                ``None``, will use the maximum timestamp in the data.
                If set to ``"entity"``, will use the timestamp of the entity.
            context_anchor_time: The maximum anchor timestamp for context
                examples. If set to ``None``, ``anchor_time`` will
                determine the anchor time for context examples.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            max_pq_iterations: The maximum number of iterations to perform to
                collect valid labels. It is advised to increase the number of
                iterations in case the predictive query has strict entity
                filters, in which case, :class:`KumoRFM` needs to sample more
                entities to find valid labels.
            random_seed: A manual seed for generating pseudo-random numbers.
            verbose: Whether to print verbose output.
            use_prediction_time: Whether to use the anchor timestamp as an
                additional feature during prediction. This is typically
                beneficial for time series forecasting tasks.

        Returns:
            The metrics as a :class:`pandas.DataFrame`
        """
        query_def = replace(
            self._parse_query(query),
            for_each='FOR EACH',
            rfm_entity_ids=None,
        )

        if not isinstance(verbose, ProgressLogger):
            query_repr = query_def.to_string(rich=True, exclude_predict=True)
            msg = f'[bold]EVALUATE[/bold] {query_repr}'
            verbose = ProgressLogger.default(msg=msg, verbose=verbose)

        with verbose as logger:
            task_table = self._get_task_table(
                query=query_def,
                indices=None,
                anchor_time=anchor_time,
                context_anchor_time=context_anchor_time,
                run_mode=run_mode,
                max_pq_iterations=max_pq_iterations,
                random_seed=random_seed,
                logger=logger,
            )

            return self.evaluate_task(
                task_table,
                metrics=metrics,
                run_mode=run_mode,
                num_neighbors=num_neighbors,
                num_hops=num_hops,
                verbose=verbose,
                exclude_cols_dict=query_def.get_exclude_cols_dict(),
                use_prediction_time=use_prediction_time,
            )

    def evaluate_task(
        self,
        task: TaskTable,
        *,
        metrics: list[str] | None = None,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        num_hops: int = 2,
        verbose: bool | ProgressLogger = True,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        use_prediction_time: bool = False,
    ) -> pd.DataFrame:
        """Evaluates a custom task specification.

        Args:
            task: The custom :class:`TaskTable`.
            metrics: The metrics to use.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            verbose: Whether to print verbose output.
            exclude_cols_dict: Any column in any table to exclude from the
                model input.
            use_prediction_time: Whether to use the anchor timestamp as an
                additional feature during prediction. This is typically
                beneficial for time series forecasting tasks.

        Returns:
            The metrics as a :class:`pandas.DataFrame`
        """
        if num_hops != 2 and num_neighbors is not None:
            warnings.warn(f"Received custom 'num_neighbors' option; ignoring "
                          f"custom 'num_hops={num_hops}' option")
        if num_neighbors is None:
            key = RunMode.FAST if task.task_type.is_link_pred else run_mode
            num_neighbors = _DEFAULT_NUM_NEIGHBORS[key][:num_hops]

        if metrics is not None and len(metrics) > 0:
            self._validate_metrics(metrics, task.task_type)
            metrics = list(dict.fromkeys(metrics))

        if not isinstance(verbose, ProgressLogger):
            if task.task_type == TaskType.BINARY_CLASSIFICATION:
                task_type_repr = 'binary classification'
            elif task.task_type == TaskType.MULTICLASS_CLASSIFICATION:
                task_type_repr = 'multi-class classification'
            elif task.task_type == TaskType.REGRESSION:
                task_type_repr = 'regression'
            elif task.task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                task_type_repr = 'link prediction'
            else:
                task_type_repr = str(task.task_type)

            msg = f"Evaluating {task_type_repr} task"
            verbose = ProgressLogger.default(msg=msg, verbose=verbose)

        with verbose as logger:
            if task.num_context_examples > _MAX_CONTEXT_SIZE[run_mode]:
                logger.log(f"Sub-sampled {_MAX_CONTEXT_SIZE[run_mode]:,} "
                           f"out of {task.num_context_examples:,} in-context "
                           f"examples")
                task = task.narrow_context(0, _MAX_CONTEXT_SIZE[run_mode])

            if task.num_prediction_examples > _MAX_TEST_SIZE[task.task_type]:
                logger.log(f"Sub-sampled {_MAX_TEST_SIZE[task.task_type]:,} "
                           f"out of {task.num_prediction_examples:,} test "
                           f"examples")
                task = task.narrow_prediction(
                    start=0,
                    length=_MAX_TEST_SIZE[task.task_type],
                )

            context = self._get_context(
                task=task,
                run_mode=run_mode,
                num_neighbors=num_neighbors,
                exclude_cols_dict=exclude_cols_dict,
            )

            request = RFMEvaluateRequest(
                context=context,
                run_mode=RunMode(run_mode),
                metrics=metrics,
                use_prediction_time=use_prediction_time,
            )
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='Protobuf gencode')
                request_msg = request.to_protobuf()
                request_bytes = request_msg.SerializeToString()
            logger.log(f"Generated context of size "
                       f"{len(request_bytes) / (1024*1024):.2f}MB")

            if len(request_bytes) > _MAX_SIZE:
                stats_msg = Context.get_memory_stats(request_msg.context)
                raise ValueError(_SIZE_LIMIT_MSG.format(stats=stats_msg))

            for attempt in range(self._num_retries + 1):
                try:
                    resp = self._api_client.evaluate(request_bytes)
                    break
                except HTTPException as e:
                    if attempt == self._num_retries:
                        try:
                            msg = json.loads(e.detail)['detail']
                        except Exception:
                            msg = e.detail
                        raise RuntimeError(
                            f"An unexpected exception occurred. Please create "
                            f"an issue at "
                            f"'https://github.com/kumo-ai/kumo-rfm'. {msg}"
                        ) from None

                    time.sleep(2**attempt)  # 1s, 2s, 4s, 8s, ...

        return pd.DataFrame.from_dict(
            resp.metrics,
            orient='index',
            columns=['value'],
        ).reset_index(names='metric')

    def get_train_table(
        self,
        query: str,
        size: int,
        *,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        random_seed: int | None = _RANDOM_SEED,
        max_iterations: int = 10,
    ) -> pd.DataFrame:
        """Returns the labels of a predictive query for a specified anchor
        time.

        Args:
            query: The predictive query.
            size: The maximum number of entities to generate labels for.
            anchor_time: The anchor timestamp for the query. If set to
                :obj:`None`, will use the maximum timestamp in the data.
                If set to :`"entity"`, will use the timestamp of the entity.
            random_seed: A manual seed for generating pseudo-random numbers.
            max_iterations: The number of steps to run before aborting.

        Returns:
            The labels as a :class:`pandas.DataFrame`.
        """
        query_def = self._parse_query(query)

        if anchor_time is None:
            anchor_time = self._get_default_anchor_time(query_def)
            if query_def.target_ast.date_offset_range is not None:
                offset = query_def.target_ast.date_offset_range.end_date_offset
                offset *= query_def.num_forecasts
                anchor_time -= offset

        assert anchor_time is not None
        if isinstance(anchor_time, pd.Timestamp):
            self._validate_time(query_def, anchor_time, None, evaluate=True)
        else:
            assert anchor_time == 'entity'
            if query_def.entity_table not in self._sampler.time_column_dict:
                raise ValueError(f"Anchor time 'entity' requires the entity "
                                 f"table '{query_def.entity_table}' "
                                 f"to have a time column")

        train, test = self._sampler.sample_target(
            query=query_def,
            num_train_examples=0,
            train_anchor_time=anchor_time,
            num_train_trials=0,
            num_test_examples=size,
            test_anchor_time=anchor_time,
            num_test_trials=max_iterations * size,
            random_seed=random_seed,
        )

        return pd.DataFrame({
            'ENTITY': test.entity_pkey,
            'ANCHOR_TIMESTAMP': test.anchor_time,
            'TARGET': test.target,
        })

    # Helpers #################################################################

    def _parse_query(
        self,
        query: str | ValidatedPredictiveQuery,
    ) -> ValidatedPredictiveQuery:
        if isinstance(query, ValidatedPredictiveQuery):
            return query

        if isinstance(query, str) and query.strip()[:9].lower() == 'evaluate ':
            raise ValueError("'EVALUATE PREDICT ...' queries are not "
                             "supported in the SDK. Instead, use either "
                             "`predict()` or `evaluate()` methods to perform "
                             "predictions or evaluations.")

        request = RFMParseQueryRequest(
            query=query,
            graph_definition=self._graph_def,
        )

        for attempt in range(self._num_retries + 1):
            try:
                resp = self._api_client.parse_query(request)
                break
            except HTTPException as e:
                if attempt == self._num_retries:
                    try:
                        msg = json.loads(e.detail)['detail']
                    except Exception:
                        msg = e.detail
                    raise ValueError(f"Failed to parse query '{query}'. {msg}")

                time.sleep(2**attempt)  # 1s, 2s, 4s, 8s, ...

        if len(resp.validation_response.warnings) > 0:
            msg = '\n'.join([
                f'{i+1}. {warning.title}: {warning.message}'
                for i, warning in enumerate(resp.validation_response.warnings)
            ])
            warnings.warn(f"Encountered the following warnings during "
                          f"parsing:\n{msg}")

        return resp.query

    @staticmethod
    def _get_task_type(
        query: ValidatedPredictiveQuery,
        edge_types: list[tuple[str, str, str]],
    ) -> TaskType:
        if isinstance(query.target_ast, (Condition, LogicalOperation)):
            return TaskType.BINARY_CLASSIFICATION

        target = query.target_ast
        if isinstance(target, Join):
            target = target.rhs_target
        if isinstance(target, Aggregation):
            if target.aggr == AggregationType.LIST_DISTINCT:
                table_name, col_name = target._get_target_column_name().split(
                    '.')
                target_edge_types = [
                    edge_type for edge_type in edge_types
                    if edge_type[0] == table_name and edge_type[1] == col_name
                ]
                if len(target_edge_types) != 1:
                    raise NotImplementedError(
                        f"Multilabel-classification queries based on "
                        f"'LIST_DISTINCT' are not supported yet. If you "
                        f"planned to write a link prediction query instead, "
                        f"make sure to register '{col_name}' as a "
                        f"foreign key.")
                return TaskType.TEMPORAL_LINK_PREDICTION

            return TaskType.REGRESSION

        assert isinstance(target, Column)

        if target.stype in {Stype.ID, Stype.categorical}:
            return TaskType.MULTICLASS_CLASSIFICATION

        if target.stype in {Stype.numerical}:
            return TaskType.REGRESSION

        raise NotImplementedError("Task type not yet supported")

    def _get_default_anchor_time(
        self,
        query: ValidatedPredictiveQuery | None = None,
    ) -> pd.Timestamp:
        if query is not None and query.query_type == QueryType.TEMPORAL:
            aggr_table_names = [
                aggr._get_target_column_name().split('.')[0]
                for aggr in query.get_all_target_aggregations()
            ]
            return self._sampler.get_max_time(aggr_table_names)

        return self._sampler.get_max_time()

    def _validate_time(
        self,
        query: ValidatedPredictiveQuery,
        anchor_time: pd.Timestamp,
        context_anchor_time: pd.Timestamp | None,
        evaluate: bool,
    ) -> None:

        if len(self._sampler.time_column_dict) == 0:
            return  # Graph without timestamps

        if query.query_type == QueryType.TEMPORAL:
            aggr_table_names = [
                aggr._get_target_column_name().split('.')[0]
                for aggr in query.get_all_target_aggregations()
            ]
            min_time = self._sampler.get_min_time(aggr_table_names)
            max_time = self._sampler.get_max_time(aggr_table_names)
        else:
            min_time = self._sampler.get_min_time()
            max_time = self._sampler.get_max_time()

        if anchor_time < min_time:
            raise ValueError(f"Anchor timestamp '{anchor_time}' is before "
                             f"the earliest timestamp '{min_time}' in the "
                             f"data.")

        if context_anchor_time is not None and context_anchor_time < min_time:
            raise ValueError(f"Context anchor timestamp is too early or "
                             f"aggregation time range is too large. To make "
                             f"this prediction, we would need data back to "
                             f"'{context_anchor_time}', however, your data "
                             f"only contains data back to '{min_time}'.")

        if query.target_ast.date_offset_range is not None:
            end_offset = query.target_ast.date_offset_range.end_date_offset
        else:
            end_offset = pd.DateOffset(0)
        end_offset = end_offset * query.num_forecasts

        if (context_anchor_time is not None
                and context_anchor_time > anchor_time):
            warnings.warn(f"Context anchor timestamp "
                          f"(got '{context_anchor_time}') is set to a later "
                          f"date than the prediction anchor timestamp "
                          f"(got '{anchor_time}'). Please make sure this is "
                          f"intended.")
        elif (query.query_type == QueryType.TEMPORAL
              and context_anchor_time is not None
              and context_anchor_time + end_offset > anchor_time):
            warnings.warn(f"Aggregation for context examples at timestamp "
                          f"'{context_anchor_time}' will leak information "
                          f"from the prediction anchor timestamp "
                          f"'{anchor_time}'. Please make sure this is "
                          f"intended.")

        elif (context_anchor_time is not None
              and context_anchor_time - end_offset < min_time):
            _time = context_anchor_time - end_offset
            warnings.warn(f"Context anchor timestamp is too early or "
                          f"aggregation time range is too large. To form "
                          f"proper input data, we would need data back to "
                          f"'{_time}', however, your data only contains "
                          f"data back to '{min_time}'.")

        if not evaluate and anchor_time > max_time + pd.DateOffset(days=1):
            warnings.warn(f"Anchor timestamp '{anchor_time}' is after the "
                          f"latest timestamp '{max_time}' in the data. Please "
                          f"make sure this is intended.")

        if evaluate and anchor_time > max_time - end_offset:
            raise ValueError(
                f"Anchor timestamp for evaluation is after the latest "
                f"supported timestamp '{max_time - end_offset}'.")

    def _get_task_table(
        self,
        query: ValidatedPredictiveQuery,
        indices: list[str] | list[float] | list[int] | None,
        anchor_time: pd.Timestamp | Literal['entity'] | None = None,
        context_anchor_time: pd.Timestamp | None = None,
        run_mode: RunMode = RunMode.FAST,
        max_pq_iterations: int = 10,
        random_seed: int | None = _RANDOM_SEED,
        logger: ProgressLogger | None = None,
    ) -> TaskTable:

        task_type = self._get_task_type(
            query=query,
            edge_types=self._sampler.edge_types,
        )

        num_train_examples = _MAX_CONTEXT_SIZE[run_mode]
        num_test_examples = _MAX_TEST_SIZE[task_type] if indices is None else 0

        if logger is not None:
            if task_type == TaskType.BINARY_CLASSIFICATION:
                task_type_repr = 'binary classification'
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                task_type_repr = 'multi-class classification'
            elif task_type == TaskType.REGRESSION:
                task_type_repr = 'regression'
            elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                task_type_repr = 'link prediction'
            else:
                task_type_repr = str(task_type)
            logger.log(f"Identified {query.query_type} {task_type_repr} task")

        if query.target_ast.date_offset_range is None:
            step_offset = pd.DateOffset(0)
        else:
            step_offset = query.target_ast.date_offset_range.end_date_offset
        end_offset = step_offset * query.num_forecasts

        if anchor_time is None:
            anchor_time = self._get_default_anchor_time(query)
            if num_test_examples > 0:
                anchor_time = anchor_time - end_offset

            if logger is not None:
                assert isinstance(anchor_time, pd.Timestamp)
                if anchor_time == pd.Timestamp.min:
                    pass  # Static graph
                elif (anchor_time.hour == 0 and anchor_time.minute == 0
                      and anchor_time.second == 0
                      and anchor_time.microsecond == 0):
                    logger.log(f"Derived anchor time {anchor_time.date()}")
                else:
                    logger.log(f"Derived anchor time {anchor_time}")

        if isinstance(anchor_time, pd.Timestamp):
            if context_anchor_time == 'entity':
                raise ValueError("Anchor time 'entity' needs to be shared "
                                 "for context and prediction examples")
            if context_anchor_time is None:
                context_anchor_time = anchor_time - end_offset
            self._validate_time(query, anchor_time, context_anchor_time,
                                evaluate=num_test_examples > 0)
        else:
            assert anchor_time == 'entity'
            if query.query_type != QueryType.STATIC:
                raise ValueError("Anchor time 'entity' is only valid for "
                                 "static predictive queries")
            if query.entity_table not in self._sampler.time_column_dict:
                raise ValueError(f"Anchor time 'entity' requires the entity "
                                 f"table '{query.entity_table}' to "
                                 f"have a time column")
            if isinstance(context_anchor_time, pd.Timestamp):
                raise ValueError("Anchor time 'entity' needs to be shared "
                                 "for context and prediction examples")
            context_anchor_time = 'entity'

        train, test = self._sampler.sample_target(
            query=query,
            num_train_examples=num_train_examples,
            train_anchor_time=context_anchor_time,
            num_train_trials=max_pq_iterations * num_train_examples,
            num_test_examples=num_test_examples,
            test_anchor_time=anchor_time,
            num_test_trials=max_pq_iterations * num_test_examples,
            random_seed=random_seed,
        )
        train_pkey, train_time, train_y = train
        test_pkey, test_time, test_y = test

        if num_test_examples > 0 and logger is not None:
            if task_type == TaskType.BINARY_CLASSIFICATION:
                pos = 100 * int((test_y > 0).sum()) / len(test_y)
                msg = (f"Collected {len(test_y):,} test examples with "
                       f"{pos:.2f}% positive cases")
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                msg = (f"Collected {len(test_y):,} test examples holding "
                       f"{test_y.nunique()} classes")
            elif task_type == TaskType.REGRESSION:
                _min, _max = float(test_y.min()), float(test_y.max())
                msg = (f"Collected {len(test_y):,} test examples with targets "
                       f"between {format_value(_min)} and "
                       f"{format_value(_max)}")
            elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                num_rhs = test_y.explode().nunique()
                msg = (f"Collected {len(test_y):,} test examples with "
                       f"{num_rhs:,} unique items")
            else:
                raise NotImplementedError
            logger.log(msg)

        if num_test_examples == 0:
            assert indices is not None
            test_pkey = pd.Series(indices, dtype=train_pkey.dtype)
            if isinstance(anchor_time, pd.Timestamp):
                test_time = pd.Series([anchor_time]).repeat(
                    len(indices)).reset_index(drop=True)
            else:
                train_time = test_time = 'entity'

        if logger is not None:
            if task_type == TaskType.BINARY_CLASSIFICATION:
                pos = 100 * int((train_y > 0).sum()) / len(train_y)
                msg = (f"Collected {len(train_y):,} in-context examples with "
                       f"{pos:.2f}% positive cases")
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                msg = (f"Collected {len(train_y):,} in-context examples "
                       f"holding {train_y.nunique()} classes")
            elif task_type == TaskType.REGRESSION:
                _min, _max = float(train_y.min()), float(train_y.max())
                msg = (f"Collected {len(train_y):,} in-context examples with "
                       f"targets between {format_value(_min)} and "
                       f"{format_value(_max)}")
            elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                num_rhs = train_y.explode().nunique()
                msg = (f"Collected {len(train_y):,} in-context examples with "
                       f"{num_rhs:,} unique items")
            else:
                raise NotImplementedError
            logger.log(msg)

        entity_table_names: tuple[str] | tuple[str, str]
        if task_type.is_link_pred:
            final_aggr = query.get_final_target_aggregation()
            assert final_aggr is not None
            edge_fkey = final_aggr._get_target_column_name()
            for edge_type in self._sampler.edge_types:
                if edge_fkey == f'{edge_type[0]}.{edge_type[1]}':
                    entity_table_names = (
                        query.entity_table,
                        edge_type[2],
                    )
        else:
            entity_table_names = (query.entity_table, )

        context_df = pd.DataFrame({'ENTITY': train_pkey, 'TARGET': train_y})
        if isinstance(train_time, pd.Series):
            context_df['ANCHOR_TIMESTAMP'] = train_time
        pred_df = pd.DataFrame({'ENTITY': test_pkey})
        if num_test_examples > 0:
            pred_df['TARGET'] = test_y
        if isinstance(test_time, pd.Series):
            pred_df['ANCHOR_TIMESTAMP'] = test_time

        return TaskTable(
            task_type=task_type,
            context_df=context_df,
            pred_df=pred_df,
            entity_table_name=entity_table_names,
            entity_column='ENTITY',
            target_column='TARGET',
            time_column='ANCHOR_TIMESTAMP' if isinstance(
                train_time, pd.Series) else TaskTable.ENTITY_TIME,
        )

    def _get_context(
        self,
        task: TaskTable,
        run_mode: RunMode | str = RunMode.FAST,
        num_neighbors: list[int] | None = None,
        exclude_cols_dict: dict[str, list[str]] | None = None,
        top_k: int | None = None,
    ) -> Context:

        if num_neighbors is None:
            key = RunMode.FAST if task.task_type.is_link_pred else run_mode
            num_neighbors = _DEFAULT_NUM_NEIGHBORS[key][:2]

        if len(num_neighbors) > 6:
            raise ValueError(f"Cannot predict on subgraphs with more than 6 "
                             f"hops (got {len(num_neighbors)}). Reduce the "
                             f"number of hops and try again. Please create a "
                             f"feature request at "
                             f"'https://github.com/kumo-ai/kumo-rfm' if you "
                             f"must go beyond this for your use-case.")

        # Exclude the entity anchor time from the feature set to prevent
        # running out-of-distribution between in-context and test examples:
        exclude_cols_dict = copy.deepcopy(
            exclude_cols_dict) if exclude_cols_dict else {}
        if task.entity_table_name in self._sampler.time_column_dict:
            if task.entity_table_name not in exclude_cols_dict:
                exclude_cols_dict[task.entity_table_name] = []
            time_col = self._sampler.time_column_dict[task.entity_table_name]
            exclude_cols_dict[task.entity_table_name].append(time_col)

        entity_pkey = pd.concat([
            task._context_df[task._entity_column],
            task._pred_df[task._entity_column],
        ], axis=0, ignore_index=True)

        if task.use_entity_time:
            if task.entity_table_name not in self._sampler.time_column_dict:
                raise ValueError(f"The given annchor time requires the entity "
                                 f"table '{task.entity_table_name}' to have a "
                                 f"time column")
            anchor_time = 'entity'
        elif task._time_column is not None:
            anchor_time = pd.concat([
                task._context_df[task._time_column],
                task._pred_df[task._time_column],
            ], axis=0, ignore_index=True)
        else:
            anchor_time = pd.Series(self._get_default_anchor_time()).repeat(
                (len(entity_pkey))).reset_index(drop=True)

        subgraph = self._sampler.sample_subgraph(
            entity_table_names=task.entity_table_names,
            entity_pkey=entity_pkey,
            anchor_time=anchor_time,
            num_neighbors=num_neighbors,
            exclude_cols_dict=exclude_cols_dict,
        )

        if len(subgraph.table_dict) >= 15:
            raise ValueError(f"Cannot query from a graph with more than 15 "
                             f"tables (got {len(subgraph.table_dict)}). "
                             f"Please create a feature request at "
                             f"'https://github.com/kumo-ai/kumo-rfm' if you "
                             f"must go beyond this for your use-case.")

        if (task.task_type.is_link_pred
                and task.entity_table_names[-1] not in subgraph.table_dict):
            raise ValueError("Cannot perform link prediction on subgraphs "
                             "without any historical target entities. Please "
                             "increase the number of hops and try again.")

        return Context(
            task_type=task.task_type,
            entity_table_names=task.entity_table_names,
            subgraph=subgraph,
            y_train=task._context_df[task.target_column.name],
            y_test=task._pred_df[task.target_column.name]
            if task.evaluate else None,
            top_k=top_k,
            step_size=None,
        )

    @staticmethod
    def _validate_metrics(
        metrics: list[str],
        task_type: TaskType,
    ) -> None:

        if task_type == TaskType.BINARY_CLASSIFICATION:
            supported_metrics = [
                'acc', 'precision', 'recall', 'f1', 'auroc', 'auprc', 'ap'
            ]
        elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
            supported_metrics = ['acc', 'precision', 'recall', 'f1', 'mrr']
        elif task_type == TaskType.REGRESSION:
            supported_metrics = ['mae', 'mape', 'mse', 'rmse', 'smape', 'r2']
        elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
            supported_metrics = [
                'map@', 'ndcg@', 'mrr@', 'precision@', 'recall@', 'f1@',
                'hit_ratio@'
            ]
        else:
            raise NotImplementedError

        for metric in metrics:
            if '@' in metric:
                metric_split = metric.split('@')
                if len(metric_split) != 2:
                    raise ValueError(f"Unsupported metric '{metric}'. "
                                     f"Available metrics "
                                     f"are {supported_metrics}.")

                name, top_k = f'{metric_split[0]}@', metric_split[1]

                if not top_k.isdigit():
                    raise ValueError(f"Metric '{metric}' does not define a "
                                     f"valid 'top_k' value (got '{top_k}').")

                if int(top_k) <= 0:
                    raise ValueError(f"Metric '{metric}' needs to define a "
                                     f"positive 'top_k' value (got '{top_k}')")

                if int(top_k) > 100:
                    raise ValueError(f"Metric '{metric}' defines a 'top_k' "
                                     f"value greater than 100 "
                                     f"(got '{top_k}'). Please create a "
                                     f"feature request at "
                                     f"'https://github.com/kumo-ai/kumo-rfm' "
                                     f"if you must go beyond this for your "
                                     f"use-case.")

                metric = name

            if metric not in supported_metrics:
                raise ValueError(f"Unsupported metric '{metric}'. Available "
                                 f"metrics are {supported_metrics}. If you "
                                 f"feel a metric is missing, please create a "
                                 f"feature request at "
                                 f"'https://github.com/kumo-ai/kumo-rfm'.")


def format_value(value: int | float) -> str:
    if value == int(value):
        return f'{int(value):,}'
    if abs(value) >= 1000:
        return f'{value:,.0f}'
    if abs(value) >= 10:
        return f'{value:.1f}'
    return f'{value:.2f}'
