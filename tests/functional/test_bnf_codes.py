import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_bnf_codes(live_server, page: Page, sample_data):
    page.goto(live_server.url)
    expect(page).to_have_url(live_server.url + "/")

    page.get_by_role(
        "link", name="Prescribing data over time for multiple BNF Codes"
    ).click()
    expect(page).to_have_url(live_server.url + "/bnf_codes/")

    # Wait for the JS to load, just in case
    page.wait_for_load_state("networkidle")

    page.get_by_role("textbox", name="BNF codes for numerator").click()
    page.get_by_text("10 Musculoskeletal and Joint Diseases").click()
    page.get_by_text("1001 Drugs used in rheumatic").click()
    page.get_by_text("100103 Rheumatic disease").click()
    page.get_by_text("1001030 Rheumatic disease").click()
    page.get_by_text("1001030 Rheumatic disease").click(modifiers=["Shift"])
    page.get_by_text("1001030U0 Methotrexate").click(modifiers=["Shift"])
    page.get_by_role("button", name="Update query").click()
    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url(
        live_server.url
        + "/bnf_codes/?ntr_codes=1001030%0D%0A-1001030U0&ntr_product_type=all&dtr_codes=&dtr_product_type=all"
    )

    # Test if the org search works
    page.get_by_role("searchbox", name="Highlight organisation (").click()
    page.get_by_role("searchbox", name="Highlight organisation (").fill("ICB 1")
    page.get_by_role("button", name="ICB 1 ICB01 - ICB").click()

    expect(page).to_have_url(
        live_server.url
        + "/bnf_codes/?ntr_codes=1001030%0D%0A-1001030U0&ntr_product_type=all&dtr_codes=&dtr_product_type=all&org_id=ICB01"
    )
