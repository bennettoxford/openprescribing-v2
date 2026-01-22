import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"])
def test_bnf_codes(live_server, page: Page, sample_data):
    page.goto(live_server.url)
    expect(page).to_have_url(live_server.url + "/")

    page.get_by_role(
        "link", name="Prescribing data over time for multiple BNF Codes"
    ).click()
    expect(page).to_have_url(live_server.url + "/bnf_codes/")

    # Wait for the JS to load, just in case
    page.wait_for_load_state("networkidle")

    page.get_by_role("textbox", name="BNF code").click()
    page.get_by_role("textbox", name="BNF code").fill("1001030U0AA\n-1001030U0AAACAC\n")
    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url(
        live_server.url
        + "/bnf_codes/?codes=1001030U0AA%0D%0A-1001030U0AAACAC%0D%0A&product_type=all"
    )
