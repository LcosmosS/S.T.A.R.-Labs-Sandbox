"""Read-only format parsers extracted from pinned legacy helpers; no governance entrypoints."""
from __future__ import annotations
import math
from pathlib import Path
from collections import Counter

def read_bytes(path):
    return Path(path).read_bytes()


def _fits_value(card: str):
    """Parse a FITS value card as a scalar, or return None for a non-value card."""
    if card[8:10] != "= ":
        return None
    raw = card[10:].split("/", 1)[0].strip()
    if raw.startswith("'"):
        return raw.strip().strip("'").strip()
    if raw in {"T", "F"}:
        return raw == "T"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw.replace("D", "E"))
        except ValueError:
            return raw


def fits_hdus(path: Path) -> list[dict[str, object]]:
    """Read FITS HDU headers while advancing over block-padded data sections.

    Returns:
        One keyword-to-value mapping for each HDU in file order.

    Raises:
        ValueError: If the file is an LFS pointer, a header is unterminated,
            or an HDU extends beyond the file.
    """
    data = read_bytes(path)
    offset = 0
    hdus: list[dict[str, object]] = []
    while offset < len(data):
        cards: list[str] = []
        header_end = None
        for card_offset in range(offset, len(data), 80):
            card = data[card_offset : card_offset + 80].decode("ascii")
            cards.append(card)
            if card.startswith("END"):
                header_end = card_offset + 80
                break
        if header_end is None:
            raise ValueError("unterminated FITS header")
        header_size = math.ceil((header_end - offset) / 2880) * 2880
        values = {card[:8].strip(): _fits_value(card) for card in cards if card[8:10] == "= "}
        naxis = int(values.get("NAXIS", 0))
        if values.get("XTENSION") in {"BINTABLE", "TABLE"}:
            logical_size = (
                int(values.get("NAXIS1", 0)) * int(values.get("NAXIS2", 0))
                + int(values.get("PCOUNT", 0))
            ) * int(values.get("GCOUNT", 1))
        else:
            logical_size = 0 if naxis == 0 else abs(int(values.get("BITPIX", 8))) // 8
            for index in range(1, naxis + 1):
                logical_size *= int(values.get(f"NAXIS{index}", 0))
            if logical_size:
                logical_size = (logical_size + int(values.get("PCOUNT", 0))) * int(values.get("GCOUNT", 1))
        hdus.append(values)
        offset += header_size + (math.ceil(logical_size / 2880) * 2880 if logical_size else 0)
        if offset == len(data):
            break
        if offset > len(data):
            raise ValueError("FITS HDU extends beyond file")
    return hdus


def ra_degrees(value: str) -> float:
    """Convert colon- or space-separated HMS to degrees in [0, 360).

    Raises:
        ValueError: If parsing fails or the resulting angle is out of range.
    """
    h, m, s = (float(part) for part in value.replace(":", " ").split())
    result = 15.0 * (h + m / 60.0 + s / 3600.0)
    if not 0.0 <= result < 360.0:
        raise ValueError(f"RA outside [0,360): {value}")
    return result


def dec_degrees(value: str) -> float:
    """Convert signed colon- or space-separated DMS to degrees in [-90, 90].

    Raises:
        ValueError: If numeric parsing fails or the resulting angle is invalid.
    """
    parts = value.replace(":", " ").split()
    sign = -1.0 if parts[0].startswith("-") else 1.0
    d, m, s = abs(float(parts[0])), float(parts[1]), float(parts[2])
    result = sign * (d + m / 60.0 + s / 3600.0)
    if not -90.0 <= result <= 90.0:
        raise ValueError(f"Dec outside [-90,90]: {value}")
    return result


def local_name(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _stream_votable(path: Path, spec: dict) -> dict:
    try:
        from defusedxml import ElementTree as SafeET
    except ImportError as exc:
        raise RuntimeError(
            "live VizieR verification requires defusedxml; install "
            "verification/datasets/requirements.txt"
        ) from exc

    fields: list[dict[str, str]] = []
    names: list[str] = []
    by_name: dict[str, int] | None = None
    agcs: set[str] = set()
    duplicate_agc_ids = 0
    blank_agc_ids = 0
    optical_missing = 0
    optical_partial = 0
    quality: Counter = Counter()
    row_count = 0

    for _, element in SafeET.iterparse(str(path), events=("end",)):
        name = local_name(element)
        if name == "FIELD":
            fields.append(dict(element.attrib))
            element.clear()
            continue
        if name != "TR":
            continue

        if not names:
            names = [field.get("name", "") for field in fields]
            by_name = {field_name: i for i, field_name in enumerate(names)}
        cells = [
            (child.text or "").strip()
            for child in element
            if local_name(child) == "TD"
        ]
        if len(cells) != len(fields):
            raise ValueError("live VOTable row width differs from FIELD count")
        row_count += 1

        required = set(spec["required_fields"])
        if by_name is not None and required.issubset(by_name):
            agc = cells[by_name["AGC"]]
            if not agc:
                blank_agc_ids += 1
            elif agc in agcs:
                duplicate_agc_ids += 1
            else:
                agcs.add(agc)

            rao = cells[by_name["RAO"]]
            deo = cells[by_name["DEO"]]
            if bool(rao) != bool(deo):
                optical_partial += 1
            elif not rao and not deo:
                optical_missing += 1

            quality[cells[by_name["HI"]]] += 1

        element.clear()

    if not names:
        names = [field.get("name", "") for field in fields]
    field_by_name = {
        field.get("name", ""): field for field in fields if field.get("name")
    }
    return {
        "fields": fields,
        "names": names,
        "field_by_name": field_by_name,
        "rows": row_count,
        "duplicate_agc_ids": duplicate_agc_ids,
        "blank_agc_ids": blank_agc_ids,
        "paired_missing_optical_coordinates": optical_missing,
        "partial_optical_coordinate_rows": optical_partial,
        "hi_quality_code_counts": dict(sorted(quality.items())),
    }
