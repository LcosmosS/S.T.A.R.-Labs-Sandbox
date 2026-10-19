"""Elementary cohomology controls; these test algebra, not physical theories."""
import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/playground/cochains.py"
spec = importlib.util.spec_from_file_location("playground_cochains", SOURCE)
cochains = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cochains)


class FirstPrinciplesCochainTests(unittest.TestCase):
    """Verify exact/closed distinctions on precisely declared cell complexes."""

    def test_discrete_gradient_telescopes_on_closed_loop(self):
        """An exact 1-cochain has zero circulation around any oriented cycle."""
        vertices = {0: 2, 1: 5, 2: 7, 3: -1}
        values = cochains.discrete_gradient(vertices, [(0, 1), (1, 2),
                                                       (2, 3), (3, 0)])
        self.assertEqual(cochains.oriented_boundary_sum(values), 0.0)

    def test_exact_gradients_survive_large_and_float_potentials(self):
        """Exact boundary sums must telescope despite floating-point cancellation."""
        cycle = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for potentials in (
            {0: 0, 1: 10**30, 2: 1, 3: 2},
            {0: 0.0, 1: 1e16, 2: 1.0, 3: 2.0},
            {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.4},
        ):
            with self.subTest(potentials=potentials):
                gradient = cochains.discrete_gradient(potentials, cycle)
                self.assertEqual(cochains.oriented_boundary_sum(gradient), 0)
        self.assertEqual(cochains.discrete_gradient(
            {0: 10**30, 1: 10**30 + 1}, [(0, 1)]), [1])
        self.assertEqual(cochains.oriented_boundary_sum([0.25, 0.1, -0.1]),
                         Fraction(1, 4))

    def test_circle_graph_cocycle_is_closed_but_nonexact(self):
        """A nonzero loop integral obstructs exactness on a graph S1."""
        result = cochains.square_cycle_demo()
        self.assertEqual(result["candidate_form"]["boundary_integral"], 4.0)
        self.assertTrue(result["candidate_form"]["closed_on_graph"])
        self.assertFalse(result["candidate_form"]["exact_on_graph"])
        self.assertFalse(result["candidate_form"]["closed_on_filled_square"])
        self.assertEqual(result["exact_form"]["boundary_integral"], 0.0)

    def test_nonfinite_and_unknown_vertices_rejected(self):
        """Invalid potentials or edge references fail without silent repairs."""
        for value in [float("nan"), float("inf"), True, "2"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                cochains.discrete_gradient({0: value, 1: 3}, [(0, 1)])
        with self.assertRaisesRegex(ValueError, "unknown"):
            cochains.discrete_gradient({0: 1}, [(0, 1)])

    def test_demo_does_not_claim_cohomological_physics(self):
        """Check synthetic demonstration has explicit epistemic nonclaims."""
        result = cochains.square_cycle_demo()
        self.assertEqual(result["status"], "exploratory")
        self.assertEqual(result["scope"], "sandbox-only")
        self.assertFalse(result["scientific_claim"])
        self.assertFalse(result["eligible_for_automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
