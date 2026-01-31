"""Sequence cleaving logic for ProsperParser"""

from __future__ import annotations

from pyfastx import Sequence

TYPE_CHECKING = False
if TYPE_CHECKING:
    import pandas as pd
    from pyfastx import Sequence

    from .cli import ProsperParser

def search(masterlist: list[Sequence], query: str) -> tuple[list[Sequence], bool]:
    found_any = False
    newmasterlist: list[Sequence] = []
    for seq in masterlist:
        target: Sequence = seq
        a: int | None = target.search(query)
        if a is not None:
            found_any = True
        while a is not None:
            newmasterlist.append(target[: a - 1])
            target = target[a + len(query) - 1 :]
            a = target.search(query)
        newmasterlist.append(target)
    return newmasterlist, found_any

def cleave(args: ProsperParser, results: pd.DataFrame) -> set[str]:
    if args.fasta is not None:
        if args.sequence is not None:
            seq: Sequence = args.fasta[args.sequence]
            masterlist: list[Sequence] = []
            query: str
            for query in results["seqs"].drop_duplicates().array:
                a: int | None = seq.search(query)
                while a is not None:
                    masterlist.append(seq[:a-1])
                    seq = seq[a + len(query) - 1 :]
                    a = seq.search(query)
                masterlist.append(seq)
            to_search: list[str] = list(results["seqs"].drop_duplicates().array)
            while len(to_search) > 0:
                search_next = to_search.pop()
                masterlist, found_any = search(masterlist, search_next)
                if found_any is True:
                    to_search.reverse()
                    to_search.append(search_next)
                    to_search.reverse()
            return {masterlist[i].seq for i in range(len(masterlist))}
        raise TypeError(args.sequence)
    raise TypeError(args.fasta)
