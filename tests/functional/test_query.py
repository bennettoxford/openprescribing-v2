import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_query(live_server, page: Page, sample_data):
    # This is a limited smoke test that checks that codes can be selected from the table
    # (numerator) and the tree (denominator), and that on form submission we're directed
    # to the expected URL.
    page.goto(live_server.url)
    page.get_by_role("textbox", name="BNF codes for numerator").click()
    page.get_by_role("textbox", name="Search by name or code").click()
    page.get_by_role("textbox", name="Search by name or code").fill("metho")
    page.get_by_role("button", name="Search").click()
    page.get_by_text("1001030U0 Methotrexate").click()
    page.get_by_text("1001030U0AAACAC").click(modifiers=["ControlOrMeta"])
    page.locator("#bnf-table-modal").get_by_role("button", name="Update Query").click()
    page.locator("#bnf-tree-modal").get_by_role("button", name="Update Query").click()
    page.get_by_role("textbox", name="BNF codes for denominator").click()
    page.get_by_role("textbox", name="Search by name or code").click()
    page.get_by_role("textbox", name="Search by name or code").fill("metho")
    page.get_by_role("button", name="Search").click()
    page.locator("#bnf-tree-modal").get_by_text("1001030U0 Methotrexate").click(
        modifiers=["ControlOrMeta"]
    )
    page.locator("#bnf-tree-modal").get_by_role("button", name="Update Query").click()
    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url(
        live_server.url
        + "/?ntr_codes=1001030U0_AC&ntr_product_type=all&dtr_codes=1001030U0&dtr_product_type=all"
    )

    # Test org search
    page.get_by_role(
        "searchbox", name="Name or code of organisation to highlight"
    ).click()
    page.get_by_role(
        "searchbox", name="Name or code of organisation to highlight"
    ).fill("ICB 1")
    page.get_by_role("button", name="ICB 1 ICB01 - ICB").click()

    expect(page).to_have_url(
        live_server.url
        + "/?ntr_codes=1001030U0_AC&ntr_product_type=all&dtr_codes=1001030U0&dtr_product_type=all&org_id=ICB01"
    )
