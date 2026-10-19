"""Intentionally false universal implication: search for a counterexample."""
def counterexample(start=-10, stop=11):
    for n in range(start, stop):
        if n % 2 == 0 and n % 4 != 0:
            return n
    return None

if __name__ == "__main__":
    witness = counterexample()
    assert witness is not None and witness % 2 == 0 and witness % 4 != 0
    print("Counterexample to false proposition:", witness)
