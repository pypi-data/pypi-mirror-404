from collections.abc import Callable, Collection
from pathlib import Path
from typing import Literal, Self, overload

__version__: str


def gzip_check(file_name: str) -> bool: ...
def reverse_complement(*args, **kwargs): ...
def version(debug: bool = False) -> str: ...


class Sequence(Collection):
    def __iter__(self) -> Self: ...

    def __next__(self) -> str: ...

    @overload
    def __getitem__(self, key: int) -> str: ...

    @overload
    def __getitem__(self, key: slice) -> Sequence: ...

    def __len__(self) -> int: ...

    def __contains__(self, x: object) -> bool: ...

    def search(self, subseq: str, strand: Literal["+", "-"] = "+") -> int | None: ...

    id: int
    name: str
    description: str
    start: int
    end: int
    gc_content: float
    gc_skew: float
    composition: dict[str, float]
    raw: str
    seq: str
    reverse: str
    complement: str
    antisense: str



class FastaKeys:
    def __init__(self): ...


class Fasta(Collection):
    def __init__(
        self,
        file_name: str | Path,
        index_file: str | Path | None = None,
        uppercase: bool = True,
        build_index: bool = True,
        full_index: bool = False,
        full_name: bool = False,
        memory_index: bool = False,
        key_func: Callable[[str], str] | None = None,
    ): ...

    def __iter__(self) -> Self: ...

    def __next__(self) -> Sequence: ...

    def __getitem__(self, key: str | int) -> Sequence: ...

    def __len__(self) -> int: ...

    def __contains__(self, x: object) -> bool: ...

    def fetch(
        self, chrom: str, intervals: list[tuple[int, int]], strand: str = "+"
    ) -> list[str]: ...

    def flank(
        self, chrom: str, start: int, end: int, flank_length: int, use_cache: bool
    ) -> tuple[str, str]: ...

    def build_index(self) -> None: ...
    def keys(self) -> FastaKeys: ...
    def count(self, n: int) -> int: ...
    def n1(self, quantile: int) -> tuple[int, int]: ...

    file_name: str
    size: int
    type: Literal["DNA", "RNA", "protein", "unknown"]
    is_gzip: bool
    gc_content: float
    gc_skew: float
    composition: dict[str, float]
    longest: Sequence
    shortest: Sequence
    mean: int
    median: int
