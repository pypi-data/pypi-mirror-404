import copy
from collections.abc import Sequence

import pandas as pd
from kumoapi.task import TaskType
from kumoapi.typing import Dtype, Stype
from typing_extensions import Self

from kumoai.experimental.rfm.base import Column
from kumoai.experimental.rfm.infer import contains_timestamp, infer_dtype


class TaskTable:
    r"""A :class:`TaskTable` fully specifies the task, *i.e.* its context and
    prediction examples with entity IDs, targets and timestamps.

    Args:
        task_type: The task type.
        context_df: The data frame holding context examples.
        pred_df: The data frame holding prediction examples.
        entity_table_name: The entity table to predict for. For link prediction
            tasks, needs to hold both entity and target table names.
        entity_column: The name of the entity column.
        target_column: The name of the target column.
        time_column: The name of the time column to use as anchor time. If
            ``TaskTable.ENTITY_TIME``, use the timestamp of the entity table
            as anchor time.
    """
    ENTITY_TIME = '__entity_time__'

    def __init__(
        self,
        task_type: TaskType,
        context_df: pd.DataFrame,
        pred_df: pd.DataFrame,
        entity_table_name: str | Sequence[str],
        entity_column: str,
        target_column: str,
        time_column: str | None = None,
    ) -> None:

        task_type = TaskType(task_type)
        if task_type not in {  # Currently supported task types:
                TaskType.BINARY_CLASSIFICATION,
                TaskType.MULTICLASS_CLASSIFICATION,
                TaskType.REGRESSION,
                TaskType.TEMPORAL_LINK_PREDICTION,
        }:
            raise ValueError  # TODO
        self._task_type = task_type

        # TODO Binary classification and regression checks

        # TODO Check dfs (unify from local table)
        if context_df.empty:
            raise ValueError("No context examples given")
        self._context_df = context_df.copy(deep=False)

        if pred_df.empty:
            raise ValueError("Provide at least one entity to predict for")
        self._pred_df = pred_df.copy(deep=False)

        self._dtype_dict: dict[str, Dtype] = {
            column_name: infer_dtype(context_df[column_name])
            for column_name in context_df.columns
        }

        self._entity_table_names: tuple[str] | tuple[str, str]
        if isinstance(entity_table_name, str):
            self._entity_table_names = (entity_table_name, )
        elif len(entity_table_name) == 1:
            self._entity_table_names = (entity_table_name[0], )
        elif len(entity_table_name) == 2:
            self._entity_table_names = (
                entity_table_name[0],
                entity_table_name[1],
            )
        else:
            raise ValueError  # TODO

        self._entity_column: str = ''
        self._target_column: str = ''
        self._time_column: str | None = None

        self.entity_column = entity_column
        self.target_column = target_column
        if time_column is not None:
            self.time_column = time_column

        self._query: str = ''  # A description of the task, e.g., for XAI.

    @property
    def num_context_examples(self) -> int:
        return len(self._context_df)

    @property
    def num_prediction_examples(self) -> int:
        return len(self._pred_df)

    @property
    def task_type(self) -> TaskType:
        r"""The task type."""
        return self._task_type

    def narrow_context(self, start: int, length: int) -> Self:
        r"""Returns a new :class:`TaskTable` that holds a narrowed version of
        context examples.

        Args:
            start: Index of the prediction examples to start narrowing.
            length: Length of the prediction examples.
        """
        out = copy.copy(self)
        df = out._context_df.iloc[start:start + length].reset_index(drop=True)
        out._context_df = df
        return out

    def narrow_prediction(self, start: int, length: int) -> Self:
        r"""Returns a new :class:`TaskTable` that holds a narrowed version of
        prediction examples.

        Args:
            start: Index of the prediction examples to start narrowing.
            length: Length of the prediction examples.
        """
        out = copy.copy(self)
        df = out._pred_df.iloc[start:start + length].reset_index(drop=True)
        out._pred_df = df
        return out

    # Entity column ###########################################################

    @property
    def entity_table_name(self) -> str:
        return self._entity_table_names[0]

    @property
    def entity_table_names(self) -> tuple[str] | tuple[str, str]:
        return self._entity_table_names

    @property
    def entity_column(self) -> Column:
        return Column(
            name=self._entity_column,
            expr=None,
            dtype=self._dtype_dict[self._entity_column],
            stype=Stype.ID,
        )

    @entity_column.setter
    def entity_column(self, name: str) -> None:
        if name not in self._context_df:
            raise ValueError  # TODO
        if name not in self._pred_df:
            raise ValueError  # TODO
        if not Stype.ID.supports_dtype(self._dtype_dict[name]):
            raise ValueError  # TODO

        self._entity_column = name

    # Target column ###########################################################

    @property
    def evaluate(self) -> bool:
        r"""Returns ``True`` if this task can be used for model evaluation."""
        return self._target_column in self._pred_df

    @property
    def _target_stype(self) -> Stype:
        if self.task_type in {
                TaskType.BINARY_CLASSIFICATION,
                TaskType.MULTICLASS_CLASSIFICATION,
        }:
            return Stype.categorical
        if self.task_type in {TaskType.REGRESSION}:
            return Stype.numerical
        if self.task_type.is_link_pred:
            return Stype.multicategorical
        raise ValueError

    @property
    def target_column(self) -> Column:
        return Column(
            name=self._target_column,
            expr=None,
            dtype=self._dtype_dict[self._target_column],
            stype=self._target_stype,
        )

    @target_column.setter
    def target_column(self, name: str) -> None:
        if name not in self._context_df:
            raise ValueError  # TODO
        if not self._target_stype.supports_dtype(self._dtype_dict[name]):
            raise ValueError  # TODO

        self._target_column = name

    # Time column #############################################################

    def has_time_column(self) -> bool:
        r"""Returns ``True`` if this task has a time column; ``False``
        otherwise.
        """
        return self._time_column not in {None, self.ENTITY_TIME}

    @property
    def use_entity_time(self) -> bool:
        r"""Whether to use the timestamp of the entity table as anchor time."""
        return self._time_column == self.ENTITY_TIME

    @property
    def time_column(self) -> Column | None:
        r"""The time column of this task.

        The getter returns the time column of this task, or ``None`` if no
        such time column is present.

        The setter sets a column as a time column for this task, and raises a
        :class:`ValueError` if the time column has a non-timestamp compatible
        data type or if the column name does not match a column in the data
        frame.
        """
        if not self.has_time_column():
            return None
        assert self._time_column is not None
        return Column(
            name=self._time_column,
            expr=None,
            dtype=self._dtype_dict[self._time_column],
            stype=Stype.timestamp,
        )

    @time_column.setter
    def time_column(self, name: str | None) -> None:
        if name is None or name == self.ENTITY_TIME:
            self._time_column = name
            return

        if name not in self._context_df:
            raise ValueError  # TODO
        if name not in self._pred_df:
            raise ValueError  # TODO
        if not contains_timestamp(
                ser=self._context_df[name],
                column_name=name,
                dtype=self._dtype_dict[name],
        ):
            raise ValueError  # TODO

        self._time_column = name

    # Metadata ################################################################

    @property
    def metadata(self) -> pd.DataFrame:
        raise NotImplementedError

    def print_metadata(self) -> None:
        raise NotImplementedError

    # Python builtins #########################################################

    def __hash__(self) -> int:
        return hash((
            self.task_type,
            self.entity_table_names,
            self._entity_column,
            self._target_column,
            self._time_column,
        ))

    def __repr__(self) -> str:
        if self.task_type.is_link_pred:
            entity_table_repr = f'entity_table_names={self.entity_table_names}'
        else:
            entity_table_repr = f'entity_table_name={self.entity_table_name}'

        if self.use_entity_time:
            time_repr = 'use_entity_time=True'
        else:
            time_repr = f'time_column={self._time_column}'

        return (f'{self.__class__.__name__}(\n'
                f'  task_type={self.task_type},\n'
                f'  num_context_examples={self.num_context_examples},\n'
                f'  num_prediction_examples={self.num_prediction_examples},\n'
                f'  {entity_table_repr},\n'
                f'  entity_column={self._entity_column},\n'
                f'  target_column={self._target_column},\n'
                f'  {time_repr},\n'
                f')')
