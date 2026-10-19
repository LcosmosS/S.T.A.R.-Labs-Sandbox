-- DATA-SDSS18-200K deterministic independent probe
--
-- Submit this query in the DR18 CasJobs context using the Submit button and
-- provide a UNIQUE output name in the CasJobs "Table" field for each run.
-- CasJobs will create that result in MyDB. Do not add a fixed INTO target:
-- unique Table-field names make reruns collision-free without cross-context
-- DROP TABLE operations.
--
-- This is NOT a reconstruction of the historical row membership. It applies
-- the recovered schema, join, and magnitude predicates to the current DR18
-- context with an explicit order so an independent reviewer can obtain a
-- stable comparison sample. It must never replace the frozen historical CSV
-- or silently change DATA-SDSS18-200K provenance.

SELECT TOP 200000
    p.objid,
    p.ra,
    p.dec,
    p.u,
    p.g,
    p.r,
    p.i,
    p.z,
    p.run,
    p.rerun,
    p.camcol,
    p.field,
    s.specobjid,
    s.class,
    s.z AS redshift,
    s.plate,
    s.mjd,
    s.fiberid
FROM PhotoObj AS p
JOIN SpecObj AS s
    ON s.bestobjid = p.objid
WHERE
    p.u BETWEEN 0 AND 19.6
    AND p.g BETWEEN 0 AND 20
ORDER BY
    p.objid ASC,
    s.specobjid ASC;
