"""Generate the deterministic CI Cremona label fixture from pinned ecdata allcurves."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


LINE_RE = re.compile(
    r"^(?P<conductor>\d+)\s+(?P<iso>[a-z]+)\s+(?P<number>\d+)\s+"
    r"\[[^\]]+\]\s+\d+\s+\d+\s*$"
)


def representative_labels(source: Path, limit: int) -> list[str]:
    labels = []
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            match = LINE_RE.fullmatch(line.rstrip("\r\n"))
            if match is None:
                raise ValueError(f"malformed allcurves line {line_number}")
            if int(match.group("number")) != 1:
                continue
            labels.append(
                f"{match.group('conductor')}{match.group('iso')}{match.group('number')}"
            )
            if len(labels) == limit:
                break
    if len(labels) != limit:
        raise ValueError(f"requested {limit} labels, found only {len(labels)}")
    return labels


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/ecdata/allcurves/allcurves.00000-09999"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/ci_subset.csv"),
    )
    parser.add_argument("--max-labels", type=int, default=800)
    args = parser.parse_args(argv)

    if args.max_labels <= 0:
        raise SystemExit("--max-labels must be positive")
    labels = representative_labels(args.source, args.max_labels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["label"])
        writer.writerows([[label] for label in labels])

    print(
        f"wrote {len(labels)} representative labels from {args.source} "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
