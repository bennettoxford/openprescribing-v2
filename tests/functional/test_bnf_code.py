import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_bnf_code(live_server, page: Page, sample_data):
    page.goto(live_server.url)
    expect(page).to_have_url(live_server.url + "/")
    page.get_by_role(
        "link",
        name="Prescribing data over time for a single BNF Code, including BNF Code search",
    ).click()

    expect(page).to_have_url(live_server.url + "/bnf_code/")

    # Wait for the JS to load, otherwise filling the searchbox will not create
    # any buttons for us to click
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Search by medicine or product").fill(
        "methotrexate"
    )
    page.get_by_role("button", name="Methotrexate 2.5mg tablets").click()

    expect(page).to_have_url(live_server.url + "/bnf_code/?code=1001030U0AAABAB")
    expect(page.get_by_text("1001030U0AAABAB")).to_be_visible()
