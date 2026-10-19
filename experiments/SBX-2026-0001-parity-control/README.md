# SANDBOX / INTENTIONALLY FALSE CONTROL — SBX-2026-0001

## Deliberately false proposition
**False statement under test:** “For every integer `n`, if `n` is even, then `n` is divisible by 4.” This statement is *not asserted as true*. It is included to test whether a counterexample-search procedure can reject a bad universal implication.

## Falsifier
The integer **2** is even but not divisible by 4. Thus the universal implication fails. This is an elementary logical control, **not** an ACSC, ECC, BSD, GLMPCT, or physical finding.

## Method
`counterexample.py` uses only the Python standard library and searches a bounded integer interval. It should return the smallest counterexample in that search order. This experiment is intentionally small and can be run locally; repository CI does not execute experiment scripts by default.

## Limitations
A finite search cannot generally establish a universal statement. The known mathematical counterexample establishes the falsity of this one proposition, not any broader scientific model. Sandbox admission is not upstream acceptance.
