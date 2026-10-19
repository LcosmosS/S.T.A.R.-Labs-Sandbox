"""Strict parsers for John Cremona's ecdata allcurves tables."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_ALLCURVES_RE = re.compile(
    r"^(?P<conductor>\d+)\s+"
    r"(?P<isogeny>[a-z]+)\s+"
    r"(?P<number>\d+)\s+"
    r"(?P<ainvs>\[[^\]]+\])\s+"
    r"(?P<rank>\d+)\s+"
    r"(?P<torsion>\d+)\s*$"
)
_RANGE_RE = re.compile(r"^allcurves\.(\d+)-(\d+)$")


class CremonaDataError(ValueError):
    """Raised when pinned ecdata bytes do not match the expected schema."""


@dataclass(frozen=True)
class CremonaCurveRecord:
    conductor: int
    isogeny: str
    number: int
    a_invariants: tuple[int, int, int, int, int]
    rank: int
    torsion_order: int

    @property
    def label(self) -> str:
        return f"{self.conductor}{self.isogeny}{self.number}"

    @property
    def isogeny_class(self) -> str:
        return f"{self.conductor}{self.isogeny}"


def _parse_ainvariants(token: str) -> tuple[int, int, int, int, int]:
    if not token.startswith("[") or not token.endswith("]"):
        raise CremonaDataError(f"invalid a-invariants token: {token!r}")
    pieces = token[1:-1].split(",")
    if len(pieces) != 5:
        raise CremonaDataError(
            f"expected five a-invariants, got {len(pieces)}: {token!r}"
        )
    try:
        values = tuple(int(piece) for piece in pieces)
    except ValueError as exc:
        raise CremonaDataError(f"non-integral a-invariants: {token!r}") from exc
    return values


def parse_allcurves_line(line: str, *, line_number: int | None = None) -> CremonaCurveRecord:
    match = _ALLCURVES_RE.fullmatch(line.rstrip("\r\n"))
    location = f" on line {line_number}" if line_number is not None else ""
    if match is None:
        raise CremonaDataError(f"malformed allcurves record{location}: {line!r}")

    conductor = int(match.group("conductor"))
    number = int(match.group("number"))
    rank = int(match.group("rank"))
    torsion = int(match.group("torsion"))
    if conductor <= 0 or number <= 0 or rank < 0 or torsion <= 0:
        raise CremonaDataError(f"invalid non-positive allcurves field{location}")

    return CremonaCurveRecord(
        conductor=conductor,
        isogeny=match.group("isogeny"),
        number=number,
        a_invariants=_parse_ainvariants(match.group("ainvs")),
        rank=rank,
        torsion_order=torsion,
    )


def iter_allcurves(path: Path | str) -> Iterable[CremonaCurveRecord]:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise CremonaDataError(
                    f"blank line is not allowed in allcurves source: {path}:{line_number}"
                )
            yield parse_allcurves_line(line, line_number=line_number)


def load_allcurves(path: Path | str) -> list[CremonaCurveRecord]:
    return list(iter_allcurves(path))


def representative_records(
    records: Iterable[CremonaCurveRecord],
) -> list[CremonaCurveRecord]:
    """Return exactly curve number 1 from each isogeny class."""
    representatives = [record for record in records if record.number == 1]
    keys = [record.isogeny_class for record in representatives]
    if len(keys) != len(set(keys)):
        raise CremonaDataError("duplicate number-1 representative for an isogeny class")
    return representatives


def find_allcurves_chunk(
    ecdata_root: Path | str,
    conductor: int,
) -> Path:
    root = Path(ecdata_root) / "allcurves"
    if not root.is_dir():
        raise CremonaDataError(f"allcurves directory not found: {root}")
    for path in sorted(root.iterdir()):
        match = _RANGE_RE.fullmatch(path.name)
        if match and int(match.group(1)) <= conductor <= int(match.group(2)):
            return path
    raise CremonaDataError(f"no allcurves chunk covers conductor {conductor}")
