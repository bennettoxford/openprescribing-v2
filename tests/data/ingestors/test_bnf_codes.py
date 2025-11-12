import pytest

from openprescribing.data.ingestors import bnf_codes
from openprescribing.data.models import BNFCode
from tests.utils import parquet_from_dicts


@pytest.mark.django_db(databases=["data"])
def test_bnf_codes_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    data = [
        {
            "BNF_CHAPTER": "Cardiovascular System",
            "BNF_CHAPTER_CODE": "02",
            "BNF_SECTION": "Positive inotropic drugs",
            "BNF_SECTION_CODE": "0201",
            "BNF_PARAGRAPH": "Cardiac glycosides",
            "BNF_PARAGRAPH_CODE": "020101",
            "BNF_SUBPARAGRAPH": "Cardiac glycosides",
            "BNF_SUBPARAGRAPH_CODE": "0201010",
            "BNF_CHEMICAL_SUBSTANCE": "Digoxin",
            "BNF_CHEMICAL_SUBSTANCE_CODE": "0201010F0",
            "BNF_PRODUCT": "Digoxin",
            "BNF_PRODUCT_CODE": "0201010F0AA",
            "BNF_PRESENTATION": "Digoxin 50micrograms/ml oral solution",
            "BNF_PRESENTATION_CODE": "0201010F0AAAAAA",
        },
        {
            "BNF_CHAPTER": "Cardiovascular System",
            "BNF_CHAPTER_CODE": "02",
            "BNF_SECTION": "Hypertension and heart failure",
            "BNF_SECTION_CODE": "0205",
            "BNF_PARAGRAPH": "Alpha-adrenoceptor blocking drugs",
            "BNF_PARAGRAPH_CODE": "020504",
            "BNF_SUBPARAGRAPH": "Alpha-adrenoceptor blocking drugs",
            "BNF_SUBPARAGRAPH_CODE": "0205040",
            "BNF_CHEMICAL_SUBSTANCE": "Terazosin hydrochloride",
            "BNF_CHEMICAL_SUBSTANCE_CODE": "0205040V0",
            "BNF_PRODUCT": "Terazosin hydrochloride (Antihypertensive)",
            "BNF_PRODUCT_CODE": "0205040V0AA",
            "BNF_PRESENTATION": "Terazosin 2mg tablets and Terazosin 1mg tablets",
            "BNF_PRESENTATION_CODE": "0205040V0AAAAAA",
        },
    ]

    parquet_from_dicts(settings.DOWNLOAD_DIR / "bnf_codes" / "bnf_codes.parquet", data)

    bnf_codes.ingest()

    results = [
        {"code": obj.code, "level": BNFCode.Level(obj.level).name, "name": obj.name}
        for obj in BNFCode.objects.order_by("level", "code")
    ]
    assert results == [
        {
            "code": "02",
            "level": "CHAPTER",
            "name": "Cardiovascular System",
        },
        {
            "code": "0201",
            "level": "SECTION",
            "name": "Positive inotropic drugs",
        },
        {
            "code": "0205",
            "level": "SECTION",
            "name": "Hypertension and heart failure",
        },
        {
            "code": "020101",
            "level": "PARAGRAPH",
            "name": "Cardiac glycosides",
        },
        {
            "code": "020504",
            "level": "PARAGRAPH",
            "name": "Alpha-adrenoceptor blocking drugs",
        },
        {
            "code": "0201010",
            "level": "SUBPARAGRAPH",
            "name": "Cardiac glycosides",
        },
        {
            "code": "0205040",
            "level": "SUBPARAGRAPH",
            "name": "Alpha-adrenoceptor blocking drugs",
        },
        {
            "code": "0201010F0",
            "level": "CHEMICAL_SUBSTANCE",
            "name": "Digoxin",
        },
        {
            "code": "0205040V0",
            "level": "CHEMICAL_SUBSTANCE",
            "name": "Terazosin hydrochloride",
        },
        {
            "code": "0201010F0AA",
            "level": "PRODUCT",
            "name": "Digoxin",
        },
        {
            "code": "0205040V0AA",
            "level": "PRODUCT",
            "name": "Terazosin hydrochloride (Antihypertensive)",
        },
        {
            "code": "0201010F0AAAAAA",
            "level": "PRESENTATION",
            "name": "Digoxin 50micrograms/ml oral solution",
        },
        {
            "code": "0205040V0AAAAAA",
            "level": "PRESENTATION",
            "name": "Terazosin 2mg tablets and Terazosin 1mg tablets",
        },
    ]
