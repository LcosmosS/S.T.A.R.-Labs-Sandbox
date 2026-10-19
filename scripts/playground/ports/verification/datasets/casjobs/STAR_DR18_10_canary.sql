-- SciServer MCP v0.2: fixed DR18 TOP 10 canary; no INTO or remote execution in policy PR.
-- Supply a uniquely generated MyDB TableName only in a separately approved phase.
SELECT TOP 10
    CAST(p.objid AS VARCHAR(20)) AS objid,
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
    CAST(s.specobjid AS VARCHAR(20)) AS specobjid,
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
