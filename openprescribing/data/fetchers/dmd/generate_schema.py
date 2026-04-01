# This script was used to generate SCHEMA in schema.py from the XSD data associated with
# a dm+d release.  The dm+d schema has not changed for as long as we've been working
# with the data, and so this file is included in the repo for information only.

# pragma: no cover file

import xml.etree.ElementTree as ET
from pathlib import Path


XS_NS = {"xs": "http://www.w3.org/2001/XMLSchema"}


def generate_schema(path):
    return {
        file_id: generate_schema_from_file(path / f"{file_id}_v2_3.xsd")
        for file_id in ["ampp", "amp", "ingredient", "lookup", "vmpp", "vmp", "vtm"]
    }


def generate_schema_from_file(path):
    tree = ET.parse(path)
    root = tree.getroot()

    fields = {}
    for ct in root.findall("xs:complexType", XS_NS):
        assert len(ct) == 1
        fields[ct.get("name")] = [e.get("name") for e in ct[0]]

    if fields:
        schema = []
        for e0 in root.find("xs:element", XS_NS)[0][0]:
            e1 = e0[0][0][0]
            schema.append(
                {
                    "group_tag": e0.get("name"),
                    "item_tag": e1.get("name"),
                    "fields": fields[e1.get("type")],
                }
            )

    else:
        e0 = root.find("xs:element", XS_NS)
        e1 = e0[0][0][0]
        schema = [
            {
                "group_tag": e0.get("name"),
                "item_tag": e1.get("name"),
                "fields": [e.get("name") for e in e1[0][0]],
            }
        ]

    return schema


if __name__ == "__main__":
    import sys

    schema = generate_schema(Path(sys.argv[1]))
    print(schema)
