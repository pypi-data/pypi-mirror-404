"""Dataset class for Mixtrain Datasets.

This module provides a Dataset class with:
- Chainable SQL queries
- Ergonomic APIs (shuffle, filter, map, sample)
- Integration with frameworks like PyTorch and HuggingFace

Example:
    >>> from mixtrain import Dataset
    >>> # Load and query in one chain
    >>> loader = Dataset("images") \\
    ...     .query("SELECT * FROM images WHERE label = 'cat'") \\
    ...     .to_torch(batch_size=32)
    >>>
    >>> # Import from HuggingFace
    >>> ds = Dataset.from_huggingface("imdb", split="train")
    >>> ds.shuffle(42).filter(lambda x: x["label"] == 1).to_torch(batch_size=32)
"""

from __future__ import annotations

import json
import random
from typing import Any, Callable, Iterator

import duckdb
import pyarrow as pa

from .client import MixClient
from .helpers import validate_resource_name
from .types import MixType

# -----------------------------------------------------------------------------
# PyTorch conversion helpers (used by from_torch)
# -----------------------------------------------------------------------------


def _tensor_to_python(v) -> Any:
    """Convert PyTorch tensor to numpy/python (zero-copy for CPU tensors)."""
    if hasattr(v, "numpy"):
        arr = v.numpy()
        return arr.item() if arr.ndim == 0 else arr
    return v


def _get_torch_columns(item) -> list[str]:
    """Determine column names from a PyTorch dataset item."""
    if isinstance(item, dict):
        return list(item.keys())
    elif isinstance(item, tuple):
        if hasattr(item, "_fields"):  # NamedTuple
            return list(item._fields)
        elif len(item) == 2:
            return ["data", "label"]
        else:
            return [f"col_{i}" for i in range(len(item))]
    else:
        return ["data"]


def _torch_item_to_dict(item) -> dict:
    """Convert a PyTorch dataset item to a dict with python/numpy values."""
    if isinstance(item, dict):
        return {k: _tensor_to_python(v) for k, v in item.items()}
    elif isinstance(item, tuple):
        if hasattr(item, "_fields"):  # NamedTuple
            return {f: _tensor_to_python(v) for f, v in zip(item._fields, item)}
        elif len(item) == 2:
            return {
                "data": _tensor_to_python(item[0]),
                "label": _tensor_to_python(item[1]),
            }
        else:
            return {f"col_{i}": _tensor_to_python(v) for i, v in enumerate(item)}
    else:
        return {"data": _tensor_to_python(item)}


class Dataset:
    """Arrow-native dataset with chainable API.

    The Dataset class uses Apache Arrow as its core abstraction, enabling:
    - Zero-copy conversion to NumPy, PyTorch, and Pandas
    - Efficient SQL queries via DuckDB
    - Streaming iteration for large datasets
    - HuggingFace datasets interop

    Usage:
        # Reference existing dataset (lazy load)
        dataset = Dataset("training-data")
        df = dataset.to_pandas()

        # Query and chain
        loader = Dataset("images").query("SELECT * FROM images WHERE label = 1").to_torch(batch_size=32)

        # Import from various sources
        ds = Dataset.from_huggingface("imdb", split="train")
        ds = Dataset.from_pandas(df)
        ds = Dataset.from_dict({"text": [...], "label": [...]})

    Args:
        name: Name of the dataset
        client: Optional MixClient instance (creates new one if not provided)
        _response: Optional cached response from creation
    """

    def __init__(
        self,
        name: str,
        client: MixClient | None = None,
        _response: dict[str, Any] | None = None,
    ):
        """Initialize Dataset.

        Args:
            name: Name of the dataset
            client: Optional MixClient instance
            _response: Optional cached response from creation
        """
        validate_resource_name(name, "dataset")

        self.name = name
        self.client = client or MixClient()
        self._response = _response
        self._metadata: dict[str, Any] | None = None
        self._table: pa.Table | None = None

    # -------------------------------------------------------------------------
    # Arrow Core
    # -------------------------------------------------------------------------

    def to_arrow(self) -> pa.Table:
        """Get as Arrow Table (lazy-loaded, cached).

        Returns:
            PyArrow Table containing all data
        """
        if self._table is None:
            # Platform dataset: load via Iceberg
            iceberg_table = self.client.get_dataset(self.name)
            self._table = iceberg_table.scan().to_arrow()
        return self._table

    def _iter_batches(self) -> Iterator[pa.RecordBatch]:
        """Internal: iterate batches from Iceberg or in-memory table."""
        if self._table is not None:
            yield from self._table.to_batches()
        else:
            iceberg_table = self.client.get_dataset(self.name)
            yield from iceberg_table.scan().to_arrow_batch_reader()

    def _iter_batches_sized(self, size: int) -> Iterator[pa.RecordBatch]:
        """Internal: yield Arrow batches of exactly the requested size.

        Accumulates batches from source and re-chunks to the requested size.
        Last batch may be smaller than size.
        """
        accumulated: list[pa.RecordBatch] = []
        total_rows = 0

        for batch in self._iter_batches():
            accumulated.append(batch)
            total_rows += len(batch)

            while total_rows >= size:
                table = pa.Table.from_batches(accumulated)
                yield table.slice(0, size).to_batches()[0]

                remainder = table.slice(size)
                accumulated = list(remainder.to_batches()) if len(remainder) > 0 else []
                total_rows = len(remainder)

        if accumulated:
            yield pa.Table.from_batches(accumulated).to_batches()[0]

    # -------------------------------------------------------------------------
    # Iteration
    # -------------------------------------------------------------------------

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over rows. Streams from Iceberg without loading full table."""
        for batch in self._iter_batches():
            for row in batch.to_pylist():
                yield row

    def __getitem__(self, idx: int | slice) -> dict[str, Any] | "Dataset":
        """Get row by index or slice.

        Optimized to use Arrow slicing (O(1) view) when table is in memory,
        or Iceberg limited scan for platform datasets when possible.

        Args:
            idx: Integer index or slice

        Returns:
            Single row dict for integer index, new Dataset for slice

        Example:
            >>> row = ds[0]           # First row as dict
            >>> row = ds[-1]          # Last row as dict
            >>> subset = ds[10:20]    # Rows 10-19 as new Dataset
        """
        if isinstance(idx, slice):
            # For slices starting from 0 on platform datasets, use limited scan
            if self._table is None and idx.start in (None, 0) and idx.step in (None, 1):
                stop = idx.stop
                if stop is not None and stop > 0:
                    # Efficient: scan only needed rows from Iceberg
                    iceberg_table = self.client.get_dataset(self.name)
                    table = iceberg_table.scan().limit(stop).to_arrow()
                    return Dataset.from_arrow(table, f"{self.name}_slice")
            # Fall back to full table for complex slices
            table = self.to_arrow()
            start, stop, step = idx.indices(len(table))
            if step != 1:
                indices = list(range(start, stop, step))
                return Dataset.from_arrow(table.take(indices), f"{self.name}_slice")
            return Dataset.from_arrow(
                table.slice(start, stop - start), f"{self.name}_slice"
            )
        else:
            # Single index access
            if idx >= 0 and self._table is None:
                # Efficient: scan only idx+1 rows from Iceberg
                iceberg_table = self.client.get_dataset(self.name)
                table = iceberg_table.scan().limit(idx + 1).to_arrow()
                if len(table) <= idx:
                    raise IndexError(f"index {idx} out of range")
                return table.slice(idx, 1).to_pylist()[0]
            # Negative index or already loaded - use full table
            table = self.to_arrow()
            if idx < 0:
                idx = len(table) + idx
            if idx < 0 or idx >= len(table):
                raise IndexError(
                    f"index {idx} out of range for dataset with {len(table)} rows"
                )
            return table.slice(idx, 1).to_pylist()[0]

    def to_batches(self, size: int = 32) -> Iterator[dict[str, list]]:
        """Yield batches as columnar dicts. Streams for large datasets.

        Respects batch size regardless of underlying storage chunk sizes.

        Args:
            size: Target batch size

        Yields:
            Dict with column names as keys and lists of values
        """
        if size <= 0:
            raise ValueError("batch size must be positive")
        for batch in self._iter_batches_sized(size):
            yield batch.to_pydict()

    # -------------------------------------------------------------------------
    # Load from External Sources (in-memory, NOT persisted)
    # -------------------------------------------------------------------------

    @classmethod
    def from_arrow(cls, table: pa.Table, name: str = "arrow") -> "Dataset":
        """Create from Arrow table (in-memory).

        Args:
            table: PyArrow Table
            name: Optional name for the dataset

        Returns:
            Dataset backed by in-memory Arrow table
        """
        ds = cls.__new__(cls)
        ds.name = name
        ds.client = None
        ds._table = table
        ds._metadata = None
        ds._response = None
        return ds

    @classmethod
    def from_huggingface(
        cls,
        hf_dataset_name: str,
        split: str = "train",
        name: str | None = None,
    ) -> "Dataset":
        """Load from HuggingFace datasets (zero-copy, Arrow-native).

        Args:
            hf_dataset_name: HuggingFace dataset name (e.g., "imdb", "squad")
            split: Dataset split (e.g., "train", "test", "train[:100]")
            name: Optional name for the dataset (defaults to hf_dataset_name)

        Returns:
            Dataset backed by in-memory Arrow table

        Example:
            >>> ds = Dataset.from_huggingface("imdb", split="train")
            >>> loader = ds.query("SELECT * FROM imdb WHERE label = 1").to_torch()
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "HuggingFace datasets required. Install with: pip install datasets"
            )

        hf_ds = load_dataset(hf_dataset_name, split=split)
        # HuggingFace datasets use Arrow internally
        table = hf_ds.data.table
        return cls.from_arrow(table, name=name or hf_dataset_name)

    @classmethod
    def from_pandas(
        cls,
        df,
        name: str = "pandas",
    ) -> "Dataset":
        """Load from pandas DataFrame (zero-copy where possible).

        Args:
            df: Pandas DataFrame
            name: Optional name for the dataset

        Returns:
            Dataset backed by in-memory Arrow table

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({"text": ["hello", "world"], "label": [0, 1]})
            >>> ds = Dataset.from_pandas(df)
        """
        table = pa.Table.from_pandas(df)
        return cls.from_arrow(table, name=name)

    @classmethod
    def from_torch(
        cls,
        torch_dataset,
        name: str = "pytorch",
        max_rows: int | None = None,
        batch_size: int = 1000,
    ) -> "Dataset":
        """Load from PyTorch dataset (torchvision, etc.).

        Supports datasets returning dicts, tuples, namedtuples, or single values.
        Uses HuggingFace datasets for optimized Arrow streaming if available,
        otherwise falls back to batched direct conversion.

        Args:
            torch_dataset: PyTorch Dataset instance (must support indexing)
            name: Optional name for the dataset
            max_rows: Optional limit on rows to load (for large datasets)
            batch_size: Batch size for processing (reduces peak memory)

        Returns:
            Dataset backed by in-memory Arrow table

        Example:
            >>> import torchvision
            >>> mnist = torchvision.datasets.MNIST("./data", download=True)
            >>> ds = Dataset.from_torch(mnist)
        """
        n = len(torch_dataset)
        if max_rows is not None:
            n = min(n, max_rows)

        # Try HuggingFace fast path (optimized Arrow streaming)
        try:
            from datasets import Dataset as HFDataset

            def generate():
                for i in range(n):
                    yield _torch_item_to_dict(torch_dataset[i])

            hf_ds = HFDataset.from_generator(generate)
            return cls.from_arrow(hf_ds.data.table, name=name)

        except ImportError:
            pass

        # Fallback: batched direct conversion
        # Peek at first item to determine column structure
        first = torch_dataset[0]
        columns = _get_torch_columns(first)

        batches = []
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch_data: dict[str, list] = {k: [] for k in columns}

            for i in range(start, end):
                item_dict = _torch_item_to_dict(torch_dataset[i])
                for k, v in item_dict.items():
                    batch_data[k].append(v)

            batches.append(pa.RecordBatch.from_pydict(batch_data))

        return cls.from_arrow(pa.Table.from_batches(batches), name=name)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, list],
        name: str = "dict",
    ) -> "Dataset":
        """Load from Python dict (in-memory).

        Args:
            data: Dict with column names as keys and lists of values
            name: Optional name for the dataset

        Returns:
            Dataset backed by in-memory Arrow table

        Example:
            >>> ds = Dataset.from_dict({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        """
        table = pa.Table.from_pydict(data)
        return cls.from_arrow(table, name=name)

    # -------------------------------------------------------------------------
    # Upload / Persist to Platform
    # -------------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        file_path: str,
        name: str | None = None,
    ) -> "Dataset":
        """Load dataset from file (in-memory). Call save() to persist.

        Supports CSV, Parquet, and JSON files (detected by extension).

        Args:
            file_path: Path to file (csv, parquet, json)
            name: Optional name (defaults to filename without extension)

        Returns:
            In-memory Dataset

        Example:
            >>> ds = Dataset.from_file("data.csv")
            >>> ds.save("my-dataset")  # Persist to platform
        """
        import os

        from pyarrow import csv as pa_csv
        from pyarrow import json as pa_json
        from pyarrow import parquet as pq

        if name is None:
            name = os.path.splitext(os.path.basename(file_path))[0]

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            table = pa_csv.read_csv(file_path)
        elif ext == ".parquet":
            table = pq.read_table(file_path)
        elif ext == ".json" or ext == ".jsonl":
            table = pa_json.read_json(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {ext}. Use .csv, .parquet, or .json"
            )

        return cls.from_arrow(table, name)

    def save(
        self,
        name: str | None = None,
        description: str | None = None,
        column_types: dict[str, type[MixType]] | None = None,
        client: MixClient | None = None,
    ) -> "Dataset":
        """Save dataset to platform (Iceberg).

        Args:
            name: New dataset name (defaults to self.name)
            description: Optional description
            column_types: Optional dict mapping column names to MixType classes
            client: Optional MixClient instance (uses self.client if not provided)

        Returns:
            New Dataset pointing to saved version

        Example:
            >>> ds = Dataset.from_dict({"x": [1, 2, 3]})
            >>> ds.save("my-dataset", description="My dataset")
            >>>
            >>> ds = Dataset.from_huggingface("imdb").shuffle(42).filter(lambda x: x["label"] == 1)
            >>> ds.save("imdb-positive-shuffled")
        """
        target_name = name or self.name
        client = client or self.client or MixClient()

        validate_resource_name(target_name, "dataset")

        properties: dict[str, str] = {}
        if description:
            properties["description"] = description
        if column_types:
            properties["mixtrain.column_types"] = json.dumps(
                {k: v._type for k, v in column_types.items()}
            )

        from pyiceberg.exceptions import TableAlreadyExistsError

        catalog = client.get_catalog()
        table_identifier = f"{client._workspace_name}.{target_name}"

        try:
            iceberg_table = catalog.create_table(
                table_identifier, self.to_arrow().schema, properties=properties
            )
        except TableAlreadyExistsError:
            raise ValueError(
                f"Dataset '{target_name}' already exists. "
                "Use a different name or delete the existing dataset first."
            )

        iceberg_table.append(self.to_arrow())

        return Dataset(target_name, client=client)

    def append_to(self, name: str) -> "Dataset":
        """Append rows to an existing dataset on platform.

        Args:
            name: Existing dataset name

        Returns:
            Dataset pointing to the updated dataset
        """
        client = self.client or MixClient()
        iceberg_table = client.get_dataset(name)
        iceberg_table.append(self.to_arrow())
        return Dataset(name, client=client)

    # -------------------------------------------------------------------------
    # SQL Queries via DuckDB
    # -------------------------------------------------------------------------

    def query(self, sql: str, table_name: str | None = None) -> "Dataset":
        """Execute SQL query via DuckDB. Returns Dataset for chaining.

        The dataset is available by its name in the query (hyphens become underscores),
        or by a custom table_name if provided.

        Note: For large datasets, consider using filter() or map() which stream.
        query() may need to load data into memory depending on the query.

        Args:
            sql: SQL query string
            table_name: Custom table name to use in SQL (default: dataset name)

        Returns:
            New Dataset with query results

        Example:
            >>> ds = Dataset.from_arrow(table, name="images")
            >>> filtered = ds.query("SELECT * FROM images WHERE label = 'cat'")
            >>> stats = ds.query("SELECT * FROM t WHERE x > 5", table_name="t")
        """
        con = duckdb.connect()
        # Use custom name or sanitize dataset name for SQL
        table_name = table_name or self.name.replace("-", "_")

        if self._table is not None:
            # In-memory: register table directly
            con.register(table_name, self._table)
        else:
            # Platform dataset: DuckDB can scan Arrow batch reader
            iceberg_table = self.client.get_dataset(self.name)
            reader = iceberg_table.scan().to_arrow_batch_reader()
            con.register(table_name, reader)

        result = con.execute(sql).fetch_arrow_table()
        return Dataset.from_arrow(result, f"{self.name}_query")

    @classmethod
    def query_multiple(
        cls,
        datasets: dict[str, "Dataset"],
        sql: str,
    ) -> "Dataset":
        """Query across multiple datasets (JOIN, UNION, etc.).

        Args:
            datasets: Dict mapping table names to Dataset instances
                      (hyphens in names become underscores)
            sql: SQL query using the table names as defined in datasets dict

        Returns:
            New Dataset with query results

        Example:
            >>> result = Dataset.query_multiple({
            ...     "images": Dataset("image-data"),
            ...     "labels": Dataset("label-data"),
            ... }, "SELECT * FROM images i JOIN labels l ON i.id = l.image_id")
        """
        con = duckdb.connect()
        for name, ds in datasets.items():
            # Sanitize name for SQL (hyphens not allowed in unquoted identifiers)
            table_name = name.replace("-", "_")
            con.register(table_name, ds.to_arrow())
        result = con.execute(sql).fetch_arrow_table()
        return cls.from_arrow(result, "multi_query")

    def join(
        self,
        other: "Dataset",
        keys: str | list[str],
        right_keys: str | list[str] | None = None,
        join_type: str = "inner",
    ) -> "Dataset":
        """Join with another dataset. Uses Arrow Table.join().

        Args:
            other: Right table to join
            keys: Column(s) to join on from left table
            right_keys: Column(s) from right table (defaults to keys)
            join_type: "inner", "left outer", "right outer", "full outer",
                       "left semi", "right semi", "left anti", "right anti"

        Returns:
            New Dataset with joined data

        Example:
            >>> images = Dataset("images")
            >>> labels = Dataset("labels")
            >>> joined = images.join(labels, keys="id")
        """
        result = self.to_arrow().join(
            other.to_arrow(),
            keys=keys,
            right_keys=right_keys,
            join_type=join_type,
        )
        return Dataset.from_arrow(result, f"{self.name}_joined")

    # -------------------------------------------------------------------------
    # HuggingFace-Style Transforms (all return new Dataset)
    # -------------------------------------------------------------------------

    def shuffle(self, seed: int | None = None) -> "Dataset":
        """Shuffle rows. Uses Arrow table.take().

        Args:
            seed: Random seed for reproducibility

        Returns:
            New Dataset with shuffled rows

        Example:
            >>> shuffled = ds.shuffle(42)
        """
        import numpy as np

        table = self.to_arrow()
        indices = np.arange(len(table), dtype=np.int64)
        np.random.default_rng(seed).shuffle(indices)
        return Dataset.from_arrow(table.take(indices), f"{self.name}_shuffled")

    def select(self, indices: list[int]) -> "Dataset":
        """Select rows by indices. Returns new Dataset.

        Args:
            indices: List of row indices to select

        Returns:
            New Dataset with selected rows

        Example:
            >>> subset = ds.select([0, 10, 20, 30])
        """
        table = self.to_arrow().take(indices)
        return Dataset.from_arrow(table, f"{self.name}_select")

    def sample(self, n: int, seed: int | None = None) -> "Dataset":
        """Random sample. Uses Arrow table.take().

        Args:
            n: Number of rows to sample
            seed: Random seed for reproducibility

        Returns:
            New Dataset with sampled rows

        Example:
            >>> sample = ds.sample(100, seed=42)
        """
        import numpy as np

        table = self.to_arrow()
        k = min(n, len(table))
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(table), size=k, replace=False)
        return Dataset.from_arrow(table.take(indices), f"{self.name}_sample")

    def cols(self, columns: list[str]) -> "Dataset":
        """Select columns. Uses Arrow table.select().

        Args:
            columns: List of column names to select

        Returns:
            New Dataset with selected columns

        Example:
            >>> ds.cols(["text", "label"])
        """
        table = self.to_arrow().select(columns)
        return Dataset.from_arrow(table, f"{self.name}_cols")

    def head(self, n: int = 5) -> "Dataset":
        """First n rows.

        Optimized to use Iceberg limited scan for platform datasets
        (avoids loading entire table).

        Args:
            n: Number of rows to return

        Returns:
            New Dataset with first n rows
        """
        if self._table is None:
            # Platform dataset: use Iceberg limited scan
            iceberg_table = self.client.get_dataset(self.name)
            table = iceberg_table.scan().limit(n).to_arrow()
        else:
            # In-memory: Arrow slice is O(1)
            table = self._table.slice(0, n)
        return Dataset.from_arrow(table, f"{self.name}_head")

    def filter(
        self,
        fn: Callable[[dict], bool],
        batch_size: int | None = 1000,
    ) -> "Dataset":
        """Filter rows with Python callable. Streams batch-by-batch.

        Args:
            fn: Function that takes a row dict and returns bool
            batch_size: Number of rows per batch. None or 0 uses native batch sizes.

        Returns:
            New Dataset with filtered rows

        Example:
            >>> positive = ds.filter(lambda x: x["label"] == 1)
        """
        if batch_size is not None and batch_size < 0:
            raise ValueError("batch_size must be non-negative")
        batch_iter = (
            self._iter_batches()
            if not batch_size
            else self._iter_batches_sized(batch_size)
        )
        batches = []
        for batch in batch_iter:
            mask = [fn(row) for row in batch.to_pylist()]
            batches.append(batch.filter(pa.array(mask)))
        return Dataset.from_arrow(
            pa.Table.from_batches(batches), f"{self.name}_filtered"
        )

    def map(
        self,
        fn: Callable[[dict], dict],
        batch_size: int | None = 1000,
    ) -> "Dataset":
        """Apply function to each row. Streams batch-by-batch for memory efficiency.

        Args:
            fn: Function that takes a row dict and returns a transformed row dict
            batch_size: Number of rows per batch. None or 0 uses native batch sizes.

        Returns:
            New Dataset with transformed data

        Example:
            >>> with_len = ds.map(lambda x: {**x, "text_len": len(x["text"])})
        """
        if batch_size is not None and batch_size < 0:
            raise ValueError("batch_size must be non-negative")
        batch_iter = (
            self._iter_batches()
            if not batch_size
            else self._iter_batches_sized(batch_size)
        )
        batches = []
        for batch in batch_iter:
            rows = [fn(row) for row in batch.to_pylist()]
            batches.append(pa.RecordBatch.from_pylist(rows))
        return Dataset.from_arrow(pa.Table.from_batches(batches), f"{self.name}_map")

    def train_test_split(
        self,
        test_size: float = 0.2,
        seed: int | None = None,
    ) -> dict[str, "Dataset"]:
        """Split into train and test sets.

        Args:
            test_size: Fraction of data for test set (0.0 to 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dict with "train" and "test" Dataset instances

        Example:
            >>> splits = ds.train_test_split(test_size=0.2, seed=42)
            >>> train_loader = splits["train"].to_torch(batch_size=32)
            >>> test_loader = splits["test"].to_torch(batch_size=32)
        """
        table = self.to_arrow()
        indices = list(range(len(table)))
        random.Random(seed).shuffle(indices)
        split_idx = int(len(indices) * (1 - test_size))
        return {
            "train": self.select(indices[:split_idx]),
            "test": self.select(indices[split_idx:]),
        }

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def to_pandas(self) -> "pandas.DataFrame":
        """Convert to pandas DataFrame (zero-copy where possible).

        Returns:
            Pandas DataFrame
        """
        return self.to_arrow().to_pandas()

    def to_table(self) -> pa.Table:
        """Get dataset as PyArrow Table.

        Returns:
            PyArrow Table
        """
        return self.to_arrow()

    def to_tensors(self) -> dict[str, Any]:
        """Convert to dict of PyTorch tensors. Zero-copy for numeric.

        Returns:
            Dict mapping column names to tensors (numeric) or lists (other types)
        """
        import torch

        result = {}
        for name in self.to_arrow().column_names:
            col = self.to_arrow().column(name)
            try:
                # Try zero-copy via numpy first (fastest)
                arr = col.to_numpy(zero_copy_only=True)
                result[name] = torch.from_numpy(arr)
            except Exception:
                # Fallback: try to create tensor from Python list
                pylist = col.to_pylist()
                try:
                    result[name] = torch.tensor(pylist)
                except (ValueError, TypeError):
                    # Non-numeric data (strings, etc.) - keep as list
                    result[name] = pylist
        return result

    def to_torch(self, batch_size: int | None = None) -> "torch.utils.data.DataLoader":
        """Get a PyTorch DataLoader with zero-copy tensor conversion.

        Numeric columns use zero-copy conversion (Arrow → NumPy → Tensor
        shares memory). Non-numeric columns fall back to Python lists.

        Args:
            batch_size: If provided, yields batches as dicts of tensors.
                       If None, yields individual rows as dicts.

        Returns:
            PyTorch DataLoader yielding dict[str, Tensor | list]
        """
        import torch
        import torch.utils.data as td

        def batch_to_tensors(batch: pa.RecordBatch) -> dict:
            """Convert Arrow batch to dict of tensors (zero-copy for numeric)."""
            result = {}
            for i, name in enumerate(batch.schema.names):
                col = batch.column(i)
                try:
                    # Try zero-copy via numpy first (fastest)
                    arr = col.to_numpy(zero_copy_only=True)
                    result[name] = torch.from_numpy(arr)
                except Exception:
                    # Fallback: try to create tensor from Python list
                    pylist = col.to_pylist()
                    try:
                        result[name] = torch.tensor(pylist)
                    except (ValueError, TypeError):
                        # Non-numeric data (strings, etc.) - keep as list
                        result[name] = pylist
            return result

        dataset = self

        class _IterableDS(td.IterableDataset):
            def __init__(self, ds: Dataset):
                self._ds = ds

            def __iter__(self):
                if batch_size is None:
                    for row in self._ds:
                        yield row
                else:
                    for batch in self._ds._iter_batches_sized(batch_size):
                        yield batch_to_tensors(batch)

        return td.DataLoader(_IterableDS(dataset), batch_size=None)

    def to_huggingface(self) -> "datasets.Dataset":
        """Convert to HuggingFace Dataset.

        Returns:
            HuggingFace Dataset instance

        Example:
            >>> hf_ds = ds.to_huggingface()
            >>> hf_ds.push_to_hub("my-dataset")
        """
        try:
            from datasets import Dataset as HFDatasetClass
        except ImportError:
            raise ImportError(
                "HuggingFace datasets required. Install with: pip install datasets"
            )
        return HFDatasetClass(self.to_arrow())

    # -------------------------------------------------------------------------
    # Metadata and Properties (backward compatible)
    # -------------------------------------------------------------------------

    @property
    def metadata(self) -> dict[str, Any]:
        """Get dataset metadata (cached after first access).

        Returns:
            Dataset metadata dict
        """
        if self._metadata is None:
            if self._response is not None:
                self._metadata = self._response
            elif self.client is not None:
                self._metadata = self.client.get_dataset_metadata(self.name)
            else:
                # In-memory dataset
                self._metadata = {
                    "name": self.name,
                    "row_count": len(self.to_arrow()),
                    "columns": self.to_arrow().column_names,
                }
        return self._metadata

    @property
    def description(self) -> str:
        """Get dataset description."""
        return self.metadata.get("description", "")

    @property
    def row_count(self) -> int | None:
        """Get dataset row count."""
        return self.metadata.get("row_count")

    @property
    def detailed_metadata(self) -> dict[str, Any]:
        """Get detailed metadata including column types."""
        if self.client is not None:
            return self.client.get_dataset_detailed_metadata(self.name)
        return self.metadata

    @property
    def column_types(self) -> dict[str, str]:
        """Get column types for this dataset."""
        metadata = self.detailed_metadata
        return metadata.get("column_types", {})

    def set_column_types(
        self, column_types: dict[str, type[MixType]]
    ) -> dict[str, Any]:
        """Set column types for this dataset.

        Args:
            column_types: Dict mapping column names to MixType classes

        Returns:
            API response dict
        """
        column_types_str = {col: typ._type for col, typ in column_types.items()}
        return self.client.update_dataset_metadata(
            self.name, column_types=column_types_str
        )

    def update_metadata(
        self,
        description: str | None = None,
        column_types: dict[str, type[MixType]] | None = None,
    ) -> dict[str, Any]:
        """Update dataset metadata.

        Args:
            description: Optional new description
            column_types: Optional dict mapping column names to MixType classes

        Returns:
            API response dict
        """
        column_types_str = None
        if column_types:
            column_types_str = {col: typ._type for col, typ in column_types.items()}
        result = self.client.update_dataset_metadata(
            self.name, description=description, column_types=column_types_str
        )
        self._metadata = None
        return result

    def versions(self) -> list[dict[str, Any]]:
        """List available versions/snapshots.

        Returns:
            List of version metadata dicts
        """
        iceberg_table = self.client.get_dataset(self.name)
        snapshots = iceberg_table.metadata.snapshots
        return [
            {
                "snapshot_id": s.snapshot_id,
                "timestamp_ms": s.timestamp_ms,
                "summary": s.summary,
            }
            for s in snapshots
        ]

    def delete(self) -> dict[str, Any]:
        """Delete the dataset.

        Returns:
            Deletion result
        """
        self.client.delete_dataset(self.name)
        return {"status": "deleted"}

    @classmethod
    def exists(cls, name: str, client: "MixClient | None" = None) -> bool:
        """Check if a dataset exists.

        Args:
            name: Dataset name to check
            client: Optional MixClient instance

        Returns:
            True if the dataset exists, False otherwise

        Example:
            >>> if not Dataset.exists("my-dataset"):
            ...     Dataset.from_pandas(df).save("my-dataset")
        """
        if client is None:
            client = MixClient()
        response = client.list_datasets()
        datasets = response.get("data", [])
        return any(ds.get("name") == name for ds in datasets)

    def refresh(self) -> None:
        """Clear cached data and force refresh on next access."""
        self._metadata = None
        self._response = None
        self._table = None

    def __len__(self) -> int:
        """Return number of rows.

        For in-memory datasets, returns table length directly.
        For platform datasets, uses detailed_metadata to avoid loading the entire table.
        """
        # For in-memory datasets, use the table directly
        if self._table is not None:
            return len(self._table)
        # For platform datasets, use detailed metadata endpoint (single-table, not list)
        if self.client is not None:
            count = self.detailed_metadata.get("row_count")
            if count is not None:
                return count
        # Fallback: load table
        return len(self.to_arrow())

    def __repr__(self) -> str:
        return f"Dataset(name='{self.name}')"

    def __str__(self) -> str:
        return f"Dataset: {self.name}"


# -----------------------------------------------------------------------------
# Helper Functions (backward compatible)
# -----------------------------------------------------------------------------


def get_dataset(name: str, client: MixClient | None = None) -> Dataset:
    """Get a dataset reference by name.

    Args:
        name: Dataset name
        client: Optional MixClient instance

    Returns:
        Dataset proxy instance
    """
    return Dataset(name, client=client)


def list_datasets(client: MixClient | None = None) -> list[Dataset]:
    """List all datasets in the workspace.

    Args:
        client: Optional MixClient instance

    Returns:
        List of Dataset instances
    """
    if client is None:
        client = MixClient()

    response = client.list_datasets()
    datasets_data = response.get("data", [])

    return [Dataset(d["name"], client=client) for d in datasets_data]
