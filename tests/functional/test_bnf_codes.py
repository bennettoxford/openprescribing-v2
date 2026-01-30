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

    numerator_codes = page.get_by_placeholder("BNF codes for numerator")
    numerator_codes.click()
    numerator_codes.fill("1001030U0AA\n-1001030U0AAACAC\n")

    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url(
        live_server.url
        + "/bnf_codes/?ntr_codes=1001030U0AA%0D%0A-1001030U0AAACAC%0D%0A&ntr_product_type=all&dtr_codes=&dtr_product_type=all"
    )

    # Test if the org search works
    page.get_by_role(
        "searchbox", name="Name or code of organisation to highlight"
    ).click()
    page.get_by_role(
        "searchbox", name="Name or code of organisation to highlight"
    ).fill("ICB 1")
    page.get_by_role("button", name="ICB 1 ICB01 - ICB").click()

    expect(page).to_have_url(
        live_server.url
        + "/bnf_codes/?ntr_codes=1001030U0AA%0D%0A-1001030U0AAACAC%0D%0A&ntr_product_type=all&dtr_codes=&dtr_product_type=all&org_id=ICB01"
    )
