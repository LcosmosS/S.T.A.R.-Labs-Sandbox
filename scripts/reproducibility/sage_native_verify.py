"""Independent native Sage arithmetic smoke test. No conjecture support.

Run only in explicitly dispatched digest-pinned Sage image with the SHA-pinned
ecdata source. Standard-library receipt generation includes failures.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

SOURCE_SHA256="259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968"
SOURCE_SIZE=2146401
SOURCE_ROWS=64687
CONDUCTORS=(11,26,37,38,50,54,57,58)
PAT=re.compile(r"(\d+) ([a-z]+) (\d+) \[(-?\d+(?:,-?\d+){4})\] (\d+) (\d+)")
MAX_SELECTED_PER_N=2


def independent_invariants(a):
    a1,a2,a3,a4,a6=a
    b2=a1*a1+4*a2
    b4=a1*a3+2*a4
    b6=a3*a3+4*a6
    b8=a1*a1*a6+4*a2*a6-a1*a3*a4+a2*a3*a3-a4*a4
    c4=b2*b2-24*b4
    delta=-(b2*b2*b8)-8*b4**3-27*b6*b6+9*b2*b4*b6
    if delta==0:
        raise ValueError("Singular record")
    return delta,Fraction(c4**3,delta)



def check_native_values(*, label, lineno, conductor, delta, j, native_conductor, native_delta, native_j):
    """Compare exact integer/rational values without cross-library equality coercion.

    Sage QQ rationals and Python fractions.Fraction need not share equality
    semantics. Normalize Sage's numerator/denominator to Python integers first.
    Keep each discrepancy separately attributable in immutable failure receipts.
    """
    native_j_fraction = Fraction(int(native_j.numerator()), int(native_j.denominator()))
    for name, expected, actual in (
        ("conductor", conductor, native_conductor),
        ("discriminant", delta, native_delta),
        ("j_invariant", j, native_j_fraction),
    ):
        if actual != expected:
            raise ValueError(
                f"Independent native {name} mismatch for {label} at source line {lineno}: "
                f"expected={expected}; native={actual}"
            )
    return native_j_fraction


def execute(source):
    from sage.all import EllipticCurve, QQ
    data=source.read_bytes()
    if len(data)!=SOURCE_SIZE or hashlib.sha256(data).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Pinned data SHA-256 or byte-size mismatch")
    lines=data.decode("ascii").splitlines()
    if len(lines)!=SOURCE_ROWS:
        raise ValueError("Pinned data row census mismatch")
    chosen={n:[] for n in CONDUCTORS}
    for lineno,line in enumerate(lines,1):
        m=PAT.fullmatch(line)
        if m is None:
            raise ValueError("Invalid source at line %d"%lineno)
        n,cl,num,a,rank,torsion=m.groups()
        conductor=int(n)
        if conductor in chosen and len(chosen[conductor])<MAX_SELECTED_PER_N:
            chosen[conductor].append((lineno,n,cl,num,tuple(map(int,a.split(",")))))
    if any(len(group)<MAX_SELECTED_PER_N for group in chosen.values()):
        raise ValueError("Incomplete fixed native-control cohort")
    rows=[]
    for conductor in CONDUCTORS:
        for lineno,n,cl,num,ain in chosen[conductor]:
            delta,j=independent_invariants(ain)
            E=EllipticCurve(QQ,list(ain))
            native_delta=int(E.discriminant())
            native_n=int(E.conductor())
            native_j=E.j_invariant()
            label=str(n)+"."+cl+str(num)
            j_fraction=check_native_values(
                label=label, lineno=lineno, conductor=conductor, delta=delta, j=j,
                native_conductor=native_n, native_delta=native_delta, native_j=native_j,
            )
            rows.append({"line":lineno,"label":label,
                         "conductor":native_n,"discriminant":str(native_delta),
                         "j_numerator":str(j_fraction.numerator),
                         "j_denominator":str(j_fraction.denominator)})
    proc=subprocess.run(["sage","--version"],capture_output=True,text=True,timeout=30,check=False)
    return {"source_sha256":SOURCE_SHA256,"source_bytes":len(data),
            "catalog_rows":len(lines),"curves_checked":len(rows),
            "sage_version":(proc.stdout+proc.stderr).strip(),"python":platform.python_version(),
            "examples":rows}


def static_self_test():
    """Source-format and exact rational-identity check; Sage is not imported."""
    samples = (
        ("11 a 1 [0,-1,1,-10,-20] 0 5", -161051, Fraction(-122023936, 161051)),
        ("37 a 1 [0,0,1,-1,0] 1 1", 37, Fraction(110592, 37)),
    )
    for raw, expected_delta, expected_j in samples:
        match=PAT.fullmatch(raw)
        if match is None:
            raise AssertionError("Known ecdata source format rejected")
        coeff=tuple(map(int,match.group(4).split(",")))
        delta,j=independent_invariants(coeff)
        if delta != expected_delta or not isinstance(j,Fraction) or j != expected_j:
            raise AssertionError("Exact Weierstrass identity differs")
        # Mimic a Sage QQ object that deliberately rejects equality to Python Fraction.
        # The normalizer must use exact numerator/denominator accessors instead.
        class NonCoercingNativeRational:
            def numerator(self):
                return j.numerator

            def denominator(self):
                return j.denominator

            def __eq__(self, other):
                raise AssertionError("Cross-library rational equality must not be used")

        data = {
            "label": str(match.group(1)) + "." + match.group(2) + match.group(3),
            "lineno": 1,
            "conductor": int(match.group(1)),
            "delta": expected_delta,
            "j": expected_j,
            "native_conductor": int(match.group(1)),
            "native_delta": expected_delta,
            "native_j": NonCoercingNativeRational(),
        }
        if check_native_values(**data) != expected_j:
            raise AssertionError("Normalized native j-invariant incorrect")
        for field, corrupt, expected_name in (
            ("native_conductor", data["conductor"] + 1, "conductor"),
            ("native_delta", expected_delta + 1, "discriminant"),
            ("native_j", Fraction(expected_j.numerator + expected_j.denominator, expected_j.denominator), "j_invariant"),
        ):
            failing = {**data, field: corrupt}
            # Python Fraction uses attributes, unlike the Sage method API.
            if field == "native_j":
                class IncorrectNativeRational(NonCoercingNativeRational):
                    def numerator(self):
                        return expected_j.numerator + expected_j.denominator
                failing["native_j"] = IncorrectNativeRational()
            try:
                check_native_values(**failing)
            except ValueError as exc:
                if f"native {expected_name} mismatch" not in str(exc):
                    raise AssertionError("Native failure attributed to wrong field") from exc
            else:
                raise AssertionError("Known native arithmetic mismatch passed undetected")
    if PAT.fullmatch("11 a 1 [0,-1,1,-10,-20] 0 5 trailing"):
        raise AssertionError("Invalid trailing fields accepted")
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--image-digest",type=str)
    p.add_argument("--runner-commit",type=str)
    args=p.parse_args()
    if args.self_test:
        static_self_test()
        print("PASS_STATIC_NATIVE_SOURCE_PARSER; no Sage or physical inference")
        return 0
    if args.source is None or args.out is None or args.image_digest is None or args.runner_commit is None:
        p.error("--source, --out, --image-digest and --runner-commit are required unless --self-test")
    if re.fullmatch(r"[A-Za-z0-9_./:-]+@sha256:[0-9a-f]{64}",args.image_digest) is None:
        p.error("--image-digest must be a pinned image reference with sha256 digest")
    if re.fullmatch(r"[0-9a-f]{40}",args.runner_commit) is None:
        p.error("--runner-commit must be a full Git commit SHA")
    if args.out.exists():
        p.error("Output receipt must not already exist")
    receipt={"schema_version":1,"name":"sage-native-independent-arithmetic-smoke",
             "scope":"sandbox-only","scientific_support":False,
             "upstream_promotion":False,"physical_correspondence":False,
             "stage":"FAILED","error":None,
             "image_digest":args.image_digest,
             "runner_commit":args.runner_commit}
    try:
        result=execute(args.source)
        receipt.update(result)
        receipt["stage"]="PASS_NATIVE_ARITHMETIC_SUBSET_ONLY"
        code=0
    except Exception as exc:
        receipt["stage"]="FAIL"
        receipt["error"]=type(exc).__name__+": "+str(exc)
        code=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"stage":receipt["stage"],"error":receipt["error"],
                      "curves_checked":receipt.get("curves_checked")},sort_keys=True))
    return code


if __name__=="__main__":
    raise SystemExit(main())
