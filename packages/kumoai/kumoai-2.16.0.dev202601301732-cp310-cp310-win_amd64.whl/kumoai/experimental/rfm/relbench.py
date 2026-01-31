import difflib
import json
from functools import lru_cache
from urllib.request import urlopen

import pooch
import pyarrow as pa

from kumoai.experimental.rfm import Graph
from kumoai.experimental.rfm.backend.local import LocalTable

PREFIX = 'rel-'
CACHE_DIR = pooch.os_cache('relbench')
HASH_URL = ('https://raw.githubusercontent.com/snap-stanford/relbench/main/'
            'relbench/datasets/hashes.json')


@lru_cache
def get_registry() -> pooch.Pooch:
    with urlopen(HASH_URL) as r:
        hashes = json.load(r)

    return pooch.create(
        path=CACHE_DIR,
        base_url='https://relbench.stanford.edu/download/',
        registry=hashes,
    )


def from_relbench(dataset: str, verbose: bool = True) -> Graph:
    dataset = dataset.lower()
    if dataset.startswith(PREFIX):
        dataset = dataset[len(PREFIX):]

    registry = get_registry()

    datasets = [key.split('/')[0][len(PREFIX):] for key in registry.registry]
    if dataset not in datasets:
        matches = difflib.get_close_matches(dataset, datasets, n=1)
        hint = f" Did you mean '{matches[0]}'?" if len(matches) > 0 else ''
        raise ValueError(f"Unknown RelBench dataset '{dataset}'.{hint} Valid "
                         f"datasets are {str(datasets)[1:-1]}.")

    registry.fetch(
        f'{PREFIX}{dataset}/db.zip',
        processor=pooch.Unzip(extract_dir='.'),
        progressbar=verbose,
    )

    graph = Graph(tables=[])
    edges: list[tuple[str, str, str]] = []
    for path in (CACHE_DIR / f'{PREFIX}{dataset}' / 'db').glob('*.parquet'):
        data = pa.parquet.read_table(path)
        metadata = {
            key.decode('utf-8'): json.loads(value.decode('utf-8'))
            for key, value in data.schema.metadata.items()
            if key in [b"fkey_col_to_pkey_table", b"pkey_col", b"time_col"]
        }

        table = LocalTable(
            df=data.to_pandas(),
            name=path.stem,
            primary_key=metadata['pkey_col'],
            time_column=metadata['time_col'],
        )
        graph.add_table(table)

        edges.extend([
            (path.stem, fkey, dst_table)
            for fkey, dst_table in metadata['fkey_col_to_pkey_table'].items()
        ])

    for edge in edges:
        graph.link(*edge)

    return graph
