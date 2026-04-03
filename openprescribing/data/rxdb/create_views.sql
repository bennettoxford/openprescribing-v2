-- Views which only involve tables in `prescribing.duckdb` can be defined when building
-- that file, but views which involve tables in the SQLite database must be defined
-- here. These are initialised dynamically when the RXDB connection is created so
-- there's no need for any migrations.

CREATE VIEW medications AS
SELECT
    id,
    name,
    is_amp,
    vmp_id,
    vtm_id,
    cast(invalid AS boolean),
    array(
        SELECT ont.formcd
        FROM ont
        WHERE ont.vpid = vmp_id
	ORDER BY ont.formcd
    ) AS form_route_ids,
    array(
        SELECT vpi.isid
        FROM vpi
        WHERE vpi.vpid = vmp_id
	ORDER BY vpi.vpid
    ) AS ingredient_ids,
FROM (
    SELECT
        vmp.vpid AS id,
        vmp.nm AS name,
        false AS is_amp,
        vmp.vpid AS vmp_id,
        vmp.vtmid AS vtm_id,
	vmp.invalid AS invalid,
    FROM vmp

    UNION ALL

    SELECT
        amp.apid AS id,
        amp.descr AS name,
        true AS is_amp,
        vmp.vpid AS vmp_id,
        vmp.vtmid AS vtm_id,
	amp.invalid AS invalid,
    FROM amp
    JOIN vmp ON amp.vpid = vmp.vpid
);
