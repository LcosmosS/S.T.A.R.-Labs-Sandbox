#!/usr/bin/env python3
"""ECC-B01 investigator A: exact symbolic controls plus independent quadrature.
Requires sympy, numpy, scipy. No SageMath or PARI/GP.
"""
import json, sys, hashlib, platform
from pathlib import Path
import numpy as np
import sympy as sp
from scipy.integrate import quad

x,y,z,phi,psi,theta,n,q,A,B=sp.symbols('x y z phi psi theta n q A B', real=True)
results=[]
def record(fid, expected, observed, passed, detail):
    results.append(dict(fixture_id=fid,expected=str(expected),observed=str(observed),pass_=bool(passed),detail=detail))

def exterior_d_1(P, Q, vars):
    u,v=vars
    return sp.simplify(sp.diff(Q,u)-sp.diff(P,v))

def zero_residual(residual):
    """An exact symbolic residual passes only when its simplified value is zero."""
    return bool(sp.simplify(residual) == 0)

# A: torus closed one-forms; smooth entropy potential.
S=sp.cos(phi)+2*sp.sin(psi)
P=1+sp.diff(S,phi)
Q=2+sp.diff(S,psi)
record('A-01',0,exterior_d_1(sp.diff(S,phi),sp.diff(S,psi),(phi,psi)),exterior_d_1(sp.diff(S,phi),sp.diff(S,psi),(phi,psi))==0,'Exact entropy differential is closed and exact')
record('A-02',0,exterior_d_1(P,Q,(phi,psi)),exterior_d_1(P,Q,(phi,psi))==0,'Closedness of eta=dphi+2dpsi+dS')
pa=sp.integrate(P,(phi,0,2*sp.pi)).subs(psi,0)
pb=sp.integrate(Q,(psi,0,2*sp.pi)).subs(phi,0)
record('A-03','(2*pi,4*pi)',(pa,pb),sp.simplify(pa-2*sp.pi)==0 and sp.simplify(pb-4*sp.pi)==0,'Period pairing')
record('A-04','nonclosed',exterior_d_1(0,sp.sin(phi),(phi,psi)),exterior_d_1(0,sp.sin(phi),(phi,psi))!=0,'Reject nonclosed form sin(phi)dpsi')

# B: northern/southern connection and curvature on S2.
AN=n*(1-sp.cos(theta))/2
AS=-n*(1+sp.cos(theta))/2
FN=sp.diff(AN,theta); FS=sp.diff(AS,theta)
record('B-01',0,sp.simplify(FN-FS),sp.simplify(FN-FS)==0,'Patch curvatures agree')
flux=sp.integrate(FN,(theta,0,sp.pi))*2*sp.pi/(2*sp.pi)
record('B-02',n,flux,sp.simplify(flux-n)==0,'Normalized flux integral')
record('B-03',n,sp.simplify(AN-AS),sp.simplify(AN-AS-n)==0,'Overlap transition differential n dphi')
record('B-04','reject n=1/2',sp.Rational(1,2),not sp.Rational(1,2).is_integer,'Transition exp(i*n*phi) not single-valued')

# C: flat T2, orientation dphi ^ dpsi, Hodge star dphi=dpsi, dpsi=-dphi.
S2=A*sp.cos(phi)+B*sp.sin(psi)
# beta=*dS = S_phi*dpsi - S_psi*dphi; d beta=(S_phiphi+S_psipsi) dphi^dpsi
local=sp.diff(S2,phi,2)+sp.diff(S2,psi,2)
Fcoef=q+local
cflux=sp.integrate(sp.integrate(Fcoef,(phi,0,2*sp.pi)),(psi,0,2*sp.pi))
record('C-01',4*sp.pi**2*q,cflux,sp.simplify(cflux-4*sp.pi**2*q)==0,'Total flux unchanged')
record('C-02','nonzero local response',local,local!=0,'Local curvature density depends on entropy')
c03_residual=sp.simplify(sp.diff(S2+7,phi,2)+sp.diff(S2+7,psi,2)-local)
record('C-03',0,c03_residual,zero_residual(c03_residual),'Constant entropy shift invariance; zero residual required')
# Fault injection: an incorrect nonzero residual must be detected rather than passed.
c03_bad_residual=sp.simplify(c03_residual+sp.Integer(1))
record('C-03-NEG','reject nonzero residual',c03_bad_residual,not zero_residual(c03_bad_residual),'Wrong residual must fail the same zero-residual predicate')
record('C-04','cohomology independent of amplitude',sp.simplify(sp.diff(cflux,A)),sp.simplify(sp.diff(cflux,A))==0,'Flux independent of entropy amplitude')
# 3D adversarial control: F=f(z) dx^dy, dF=fprime dz^dx^dy, not closed.
f=z
record('C-05','nonclosed 3D candidate',sp.diff(f,z),sp.diff(f,z)!=0,'Reject z dx^dy on 3D domain')
# Independent numerical quadrature: B n=1 and A period
num_flux=quad(lambda t: 0.5*np.sin(t),0,np.pi,epsabs=1e-12,epsrel=1e-12)[0]
record('N-01',1,num_flux,abs(num_flux-1)<1e-10,'Independent SciPy quadrature for normalized S2 flux')
num_period=quad(lambda t:1-np.sin(t),0,2*np.pi,epsabs=1e-12,epsrel=1e-12)[0]
record('N-02',2*np.pi,num_period,abs(num_period-2*np.pi)<1e-10,'Independent SciPy quadrature for first torus period')

if __name__ == "__main__":
    path=Path(__file__).resolve()
    report={'status':'PASS' if all(r['pass_'] for r in results) else 'FAIL', 'scope':'Analytic fixtures and two independent numerical quadratures only; not a mesh convergence or physical experiment', 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'python':sys.version, 'platform':platform.platform(), 'sympy':sp.__version__, 'numpy':np.__version__, 'scipy':__import__('scipy').__version__, 'results':results}
    out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('investigator_a_results.json')
    out.write_text(json.dumps(report,indent=2,default=str))
    print(report['status'],len(results),'fixtures;',out)
    for r in results:print(r['fixture_id'], 'PASS' if r['pass_'] else 'FAIL',r['detail'])
    if report['status']!='PASS':sys.exit(1)
