"""CLI for calling into parse"""

import pathlib
from dataclasses import dataclass
from typing import Annotated, TextIO

import cappa
import pyfastx

from . import cleave, constants, parse


def valid_thresh(value: float) -> float:
    if 0 <= value <= 1:
        return value
    msg = "threshold must be a decimal probability"
    raise ValueError(msg)


def gt_zero(value: int) -> int:
    if value <= 0:
        msg = "top must be more than zero"
        raise ValueError(msg)
    return value


def valid_protease(value: list[str]) -> list[str]:
    validated: list[str] = []
    for i in range(len(value)):
        if value[i] in constants.ids:
            validated.append(value[i])
        elif value[i] in constants.names:
            validated.append(constants.dict_map[value[i]])
        else:
            msg = f"invalid protease at {i}"
            raise ValueError(msg)
    return validated

def valid_fasta(value: pathlib.Path) -> pyfastx.Fasta:
    try:
        fasta: pyfastx.Fasta = pyfastx.Fasta(value)
    except RuntimeError as ex:
        msg = "pyfastx error: " + str(ex)
        raise ValueError(msg) from ex
    if fasta.type == "protein":
        return fasta
    msg = "Not a protein FASTA"
    raise ValueError(msg)


@dataclass
class ProsperParser:
    """ProsperParser
    A program for parsing ProsperousPlus outputs"""

    input: Annotated[TextIO, cappa.Arg.required, cappa.FileMode(mode = "r", encoding = "utf-8")]
    """results.csv from ProsperousPlus"""

    output: Annotated[None | TextIO, cappa.Arg(default = None), cappa.FileMode(mode = "w", encoding = "utf-8")]
    """file to write output"""

    protease: Annotated[
        None | list[str],
        cappa.Arg(parse=[cappa.default_parse, valid_protease], action = cappa.ArgAction.append, short="-p", long=True),
    ]
    """full protein name or merops id from table S1"""

    sequence: Annotated[None | str, cappa.Arg(short="-s", long=True)]
    """sequence name for filtering output"""

    top: Annotated[
        None | int,
        cappa.Arg(parse=[cappa.default_parse, gt_zero], short="-n", long=True),
    ]
    """print top n results per sequence"""

    threshold: Annotated[
        None | float,
        cappa.Arg(
            parse=[cappa.default_parse, valid_thresh],
            short="-t",
            long=True,
        ),
    ] = None
    """Probability score cutoff"""

    fasta: Annotated[
        None | pyfastx.Fasta,
        cappa.Arg(short="-f", long=True, parse=[valid_fasta]),
    ] = None
    """FASTA file containing sequences. If given, will return result of protein cleavage rather than csv. Requires sequence."""


def run():
    args = cappa.parse(ProsperParser)
    results = parse.parse_csv(args)
    if args.fasta is not None:
        seq: set[str] = cleave.cleave(args, results)
        if args.output:
            args.output.write(repr(seq))
        print(seq)  # noqa: T201
    else:
        if args.output:
            results.to_csv(args.output)
        print(results)  # noqa: T201

