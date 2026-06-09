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
    expect(page.locator("#chart-container")).to_be_attached()

    # Clicking each chart type in turn fetches fresh data from the API and renders a
    # chart.  The container is hidden until its data loads and an SVG is drawn, so a
    # visible SVG confirms the chart rendered successfully.
    for chart_type, endpoint in [
        ("all-orgs-line", "/api/prescribing-all-orgs/"),
        ("all-orgs-dots", "/api/prescribing-all-orgs/"),
        ("medications", "/api/prescribing-medications/"),
        # Visit deciles last, because that is the first chart type to be shown.
        ("deciles", "/api/prescribing-deciles/"),
    ]:
        with page.expect_response(f"**{endpoint}**") as info:
            page.locator(f"#{chart_type}").check()
        assert info.value.ok

        expect(page.locator(f"#{chart_type}")).to_be_checked()
        expect(page.locator("#chart-container")).to_be_visible()
        expect(page.locator("#chart-container svg.marks")).to_be_visible()
