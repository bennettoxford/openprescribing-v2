import datetime
import logging

import duckdb
from django.conf import settings
from django.db import transaction

from openprescribing.data.models import IngestedFile, Org
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest(force=False):
    ods_files = settings.DOWNLOAD_DIR.glob("ods/*.parquet")
    latest_file = max(ods_files, default=None)

    if not force and (
        not latest_file or latest_file.name <= IngestedFile.get_by_name("ods")
    ):
        log.debug("Found no new data to ingest")
        return

    log.info(f"Preparing to ingest file: {latest_file.name}")

    conn = duckdb.connect()
    conn.sql(f"CREATE VIEW ods AS SELECT * FROM read_parquet({escape(latest_file)})")

    with transaction.atomic(using="data"):
        Org.objects.all().delete()
        ingest_ods(conn)
        IngestedFile.set_by_name("ods", latest_file.name)

    conn.close()

    count = Org.objects.count()
    log.info(f"Ingested {count:,} organisations in total")


def ingest_ods(conn, org_types=Org.OrgType):
    OrgType = Org.OrgType

    ORG_TYPE_QUERIES = {
        OrgType.REGION: "primaryRoleName = 'NHS ENGLAND (REGION)'",
        OrgType.ICB: "'INTEGRATED CARE BOARD' IN roleName",
        OrgType.SICBL: "'SUB ICB LOCATION' IN roleName",
        OrgType.PCN: "primaryRoleName = 'PRIMARY CARE NETWORK'",
        OrgType.PRACTICE: "'GP PRACTICE' IN roleName",
        OrgType.OTHER: "primaryRoleName = 'PRESCRIBING COST CENTRE' AND 'GP PRACTICE' NOT IN roleName",
    }

    # Create a "dummy" organisation to represent all of NHS England and set it as the
    # parent of every other organisation. This avoids needing special logic elsewhere to
    # handle national totals.
    nation = Org.objects.create(
        id="ENGLAND", org_type=OrgType.NATION, name="NHS England", inactive=False
    )

    known_ids = set()

    for org_type in org_types:
        if org_type == OrgType.NATION:
            continue

        where_clause = ORG_TYPE_QUERIES[org_type]
        results = conn.execute(
            f"""
            SELECT
                id, name, inactive,
                -- Combine the various fields which can only contain a single related
                -- org ID into a single list
                [RE4, ICB, NHSER] AS related_ids,
                -- Keep the field which can contain multiple related org IDs separate.
                -- This is used for the relationship between PCNs and Practices/Others.
                isPartnerToCode AS partner_ids
            FROM
                ods
            WHERE
                country = 'ENGLAND' AND ({where_clause})
            """
        )

        counts_by_status = {False: 0, True: 0}

        for id_, name, inactive, related_ids, partner_ids in results.fetchall():
            org = Org.objects.create(
                id=id_, org_type=org_type, name=name, inactive=inactive
            )

            if org_type is Org.OrgType.PRACTICE or org_type is Org.OrgType.OTHER:
                if len(partner_ids) <= 1:
                    related_ids.extend(partner_ids)
                else:
                    today = datetime.date.today()
                    # RO272 means PCN as noted elsewhere.
                    # RE8 means "is partner to", which appears to be the standard
                    # relationship of a Practice to a PCN.
                    sql = """
                        SELECT id FROM
                            ods,
                            UNNEST(relationships['PRESCRIBING COST CENTRE']) AS t(rel)
                        WHERE primaryRole='RO272' AND
                            rel.sourceOrgCode = $1 AND
                            rel.relationshipTypeCode = 'RE8' AND
                            rel.opStartDate <= $2 AND
                            ( rel.opEndDate >= $2 OR rel.opEndDate == '' )
                        ORDER BY rel.opStartDate ASC;
                    """
                    parent_results = conn.execute(sql, [id_, str(today)]).fetchall()

                    if len(parent_results) == 1:
                        related_ids.append(parent_results[0][0])
                    else:
                        # It's still ambiguous which PCN this Practice/Other should be
                        # attached to. This was observed with a Practice which had two
                        # PCNs - one with an opStartDate five years ago & one with an
                        # opStartDate three days ago. Neither had an opEndDate.
                        # Let's take a guess that the earlier one is missing the opEndDate
                        # and take the last matching record.
                        related_ids.append(parent_results[-1][0])

            else:
                assert len(partner_ids) == 0

            # The relations we get in the data don't specify the parent/child direction.
            # However by creating orgs in strictly hierarchical order, and by only
            # creating relationships where the target already exists we know that all
            # the relationships are child->parent.
            parent_ids = known_ids.intersection(related_ids)
            org.parents.add(nation, *parent_ids)
            known_ids.add(id_)
            counts_by_status[inactive] += 1

        total = sum(counts_by_status.values())
        log.info(
            f"Ingested {total:,} orgs of {org_type!r} "
            f"(of which {counts_by_status[False]:,} are active)"
        )
        assert total, f"No orgs of type {org_type!r} found – aborting"
