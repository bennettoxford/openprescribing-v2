import pytest
from playwright.sync_api import expect

from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


pytestmark = pytest.mark.functional


@pytest.mark.filterwarnings("ignore:All-NaN slice encountered:RuntimeWarning")
def test_analysis(live_server, page, sample_data, settings, tmp_path):
    # This is a limited smoke test that walks through building a simple analysis from
    # the landing page and verifies that the resulting analysis page renders a chart.

    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)

    page.goto(live_server.url + "/")
    page.get_by_role("link", name="Start analysing prescribing data").click()

    panel = page.locator('[data-query-panel][data-panel-prefix="ntr"]')
    panel.locator("[data-add-filter]").select_option(label="VTM")
    dropdown = panel.locator("[data-dropdown]").filter(has_text="VTM").first
    dropdown.locator("[data-dropdown-input]").fill("Aden")
    dropdown.locator("[data-dropdown-options]").select_option(label="Adenosine")

    page.locator("#summary-tab").click()
    page.get_by_role("link", name="Submit").click()
    page.wait_for_load_state("domcontentloaded")

    expect(page).to_have_url(live_server.url + "/?ntr_vtm_ids=108502004")
    expect(page.locator("#deciles-chart-container")).to_be_attached()
