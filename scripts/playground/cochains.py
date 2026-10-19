"""First-principles discrete cochain controls for ECC/RTCH exploration.

Only elementary algebraic identities are computed. No physical interpretation,
empirical cohomology, or conjecture-level conclusion is made by this code.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction


def finite(value, label):
    """Represent accepted finite values exactly, without float conversion loss."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError(f"{label} must be a real number")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{label} must be finite")
        return Fraction.from_float(value)
    return value


def discrete_gradient(potential: dict, oriented_edges: list) -> list[int | Fraction]:
    """Compute exact differences of the accepted real-valued potential data."""
    if not isinstance(potential, dict) or not potential:
        raise ValueError("potential must be a nonempty vertex-value mapping")
    values = {vertex: finite(v, f"M({vertex!r})") for vertex, v in potential.items()}
    result = []
    for pair in oriented_edges:
        if len(pair) != 2:
            raise ValueError("an oriented edge must contain two endpoints")
        tail, head = pair
        if tail not in values or head not in values:
            raise ValueError("edge references an unknown potential vertex")
        result.append(values[head] - values[tail])
    return result


def oriented_boundary_sum(edge_cochain: list[int | float | Fraction]) -> int | Fraction:
    """Accumulate cochain values exactly, so exact gradients telescope to zero."""
    if not isinstance(edge_cochain, list) or not edge_cochain:
        raise ValueError("oriented boundary must contain edge values")
    total = sum((finite(value, "cochain value") for value in edge_cochain), 0)
    return total.numerator if isinstance(total, Fraction) and total.denominator == 1 else total


def square_cycle_demo() -> dict:
    """Contrast exact 1-cochains with a nontrivial S1 graph cocycle."""
    # A directed cycle 0→1→2→3→0. As a GRAPH it has no 2-cells.
    cycle = [(0, 1), (1, 2), (2, 3), (3, 0)]
    potential = {0: 0, 1: 1, 2: 4, 3: 9}
    exact_form = discrete_gradient(potential, cycle)
    exact_circulation = oriented_boundary_sum(exact_form)
    candidate = [1.0, 1.0, 1.0, 1.0]
    loop_circulation = oriented_boundary_sum(candidate)
    # On a 1D graph without 2-cells every 1-cochain is closed (d1 = 0).
    # On the corresponding FILLED square the face is a 2-cell:
    # d1(candidate)(face) = sum(candidate on oriented boundary) = 4.
    return {
        "scope": "sandbox-only",
        "status": "exploratory",
        "scientific_claim": False,
        "independently_reviewed": False,
        "eligible_for_automatic_promotion": False,
        "topology": {
            "graph": "four-edge cycle S1 with no 2-cells",
            "filled_face": "square disk with one oriented 2-cell",
        },
        "exact_form": {
            "edge_values": exact_form,
            "boundary_integral": exact_circulation,
            "is_closed_on_graph": True,
            "is_exact_by_construction": True,
        },
        "candidate_form": {
            "edge_values": candidate,
            "boundary_integral": loop_circulation,
            "closed_on_graph": True,
            "exact_on_graph": False,
            "closed_on_filled_square": False,
        },
        "reasoning": (
            "For any globally single-valued scalar M, the oriented sum of "
            "dM around a cycle telescopes to zero. A nonzero cycle integral "
            "obstructs exactness. On a graph with no faces every 1-cochain "
            "is closed; adding a face changes the closedness condition. "
            "This algebraic illustration does not prove an entropy/physical theory."
        ),
    }


def main():
    """Print a deterministic synthetic demonstration as JSON, without promotion."""
    print(json.dumps(square_cycle_demo(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
