import csv
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree
from zipfile import ZipFile

from django.conf import settings

from openprescribing.data.utils.csv_to_parquet import csv_to_parquet
from openprescribing.data.utils.http_session import HTTPSession

from .schema import SCHEMA


log = logging.getLogger(__name__)


def fetch(directory):
    """Fetch zipped XML data from TRUD, and generate one parquet file for each dm+d
    object type."""

    url = f"https://isd.digital.nhs.uk/trud/api/v1/keys/{settings.TRUD_API_KEY}/items/24/releases"
    http = HTTPSession(
        url,
        # We start with DEBUG level logging while we're checking if there's anything new
        # to fetch
        log=log.debug,
    )
    rsp = http.get("?latest")

    release = get_single_item(rsp.json()["releases"])
    assert release["id"].startswith("nhsbsa_dmd_")
    assert release["id"].endswith(".zip")
    release_id = release["id"][11:-4]
    release_date = release["releaseDate"]
    release_dir = directory / "dmd" / f"dmd_{release_date}_{release_id}"

    if release_dir.exists():
        log.debug(f"Already fetched a file for this release: {release_id}")
        return

    # Any requests we now make will be to fetch new files so we log at INFO level
    http.log = log.info

    release_dir.mkdir(parents=True)

    with TemporaryDirectory() as tmp_name:
        tmp_dir = Path(tmp_name)
        (tmp_dir / "xml").mkdir()
        (tmp_dir / "csv").mkdir()

        zip_path = tmp_dir / release["id"]

        rsp = http.download_to_file(release["archiveFileUrl"], zip_path)
        with ZipFile(zip_path) as zf:
            zf.extractall(tmp_dir / "xml")

        extract_data_from_directory(tmp_dir, release_dir)


def extract_data_from_directory(tmp_dir, release_dir):
    """Generate parquet files in release_dir from XML files in (tmp_dir / "xml").

    This function is also useful for setting up the filesystem for testing ingestion of
    dm+d data.
    """

    for file_id, schemas in SCHEMA.items():
        extract_data_from_file(tmp_dir, release_dir, file_id, schemas)


def extract_data_from_file(tmp_dir, release_dir, file_id, schemas):
    """Generate one or more parquet files from the XML data in the file identified by
    file_id.
    """

    xml_file = get_single_item((tmp_dir / "xml").glob(f"f_{file_id}2*.xml"))
    with xml_file.open() as f:
        tree = ElementTree.parse(f)

    if len(schemas) == 1:
        # Some files contain data for a single group...
        extract_data_for_group(
            tmp_dir, release_dir, file_id, tree.getroot(), schemas[0]
        )
    else:
        # ...and some contain data for many groups.
        for ix, group_node in enumerate(tree.getroot()):
            extract_data_for_group(
                tmp_dir, release_dir, file_id, group_node, schemas[ix]
            )


def extract_data_for_group(tmp_dir, release_dir, file_id, group_node, schema):
    """Generate a parquet file containing records of single type listed in group_node.

    A group_node will have structure like this:

    <VMPS>
      <VMP>
        <VPID>28946311000001106</VPID>
        <VTMID>15219611000001105</VTMID>
        <NM>Coal tar 10% / Salicylic acid 5% in Aqueous cream</NM>
        <BASISCD>0007</BASISCD>
        <PRES_STATCD>0001</PRES_STATCD>
        <DF_INDCD>2</DF_INDCD>
      </VMP>
      <VMP>
        <VPID>28789311000001103</VPID>
        <VTMID>15219611000001105</VTMID>
        <NM>Coal tar solution 10% / Salicylic acid 5% in Aqueous cream</NM>
        <BASISCD>0007</BASISCD>
        <PRES_STATCD>0001</PRES_STATCD>
        <DF_INDCD>2</DF_INDCD>
      </VMP>
      <VMP>...</VMP>
      ...
    </VMPS>

    We convert it into a list of dicts:

    [
        {
            "vpid": "28946311000001106",
            "vtmid": "15219611000001105",
            "nm": "Coal tar 10% / Salicylic acid 5% in Aqueous cream",
            "basiscd": "0007",
            "pres_statcd": "0001",
            "df_indcd": "2",
        },
        {
            "vpid": "28789311000001103",
            "vtmid": "15219611000001105",
            "nm": "Coal tar solution 10% / Salicylic acid 5% in Aqueous cream",
            "basiscd": "0007",
            "pres_statcd": "0001",
            "df_indcd": "2",
        },
        ...
    ]

    We then write this list to a CSV file and convert that to a parquet file.
    """

    assert group_node.tag == schema["group_tag"], (
        f"{group_node.tag} != {schema['group_tag']}"
    )

    if len(group_node) == 0:
        # Some groups have no data.
        return

    assert group_node[0].tag == schema["item_tag"], (
        f"{group_node[0].tag} != {schema['item_tag']}"
    )

    headers = [fieldname.lower() for fieldname in schema["fields"]]
    records = [
        {child.tag.lower(): child.text.strip() for child in element}
        for element in group_node
    ]

    # Most groups are structured like this:
    #
    # <TAG_WE_DONT_CARE_ABOUT>
    #   <OBJ_TYPE>...</OBJ_TYPE>
    #   <OBJ_TYPE>...</OBJ_TYPE>
    # </TAG_WE_DONT_CARE_ABOUT>
    #
    # but the lookup file contains groups structured like this:
    #
    # <OBJ_TYPE>
    #   <INFO>...</INFO>
    #   <INFO>...</INFO>
    # </OBJ_TYPE>
    obj_type = group_node.tag if file_id == "lookup" else group_node[0].tag

    csv_path = tmp_dir / "csv" / f"{obj_type.lower()}.csv"
    parquet_path = release_dir / f"{obj_type.lower()}.parquet"

    with open(csv_path, "w") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(records)

    csv_to_parquet(csv_path, parquet_path)


def get_single_item(iterable):
    items = list(iterable)
    assert len(items) == 1, len(items)
    return items[0]
