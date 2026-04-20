import pytest
from playwright.sync_api import expect

from openprescribing.data.models import BNFCode
from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


pytestmark = pytest.mark.functional


STATUS_INCLUDED = "included"
STATUS_EXCLUDED = "excluded"
STATUS_NOT_INCLUDED = "not_included"


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_build_analyse_has_dynamic_filters_and_independent_queries(
    live_server, page, rxdb, settings, tmp_path
):
    # Seed a small dataset with overlapping VTM, BNF, and form/route coverage.
    rxdb.ingest(
        [
            {"bnf_code": "0203020C0BBAAAA"},
            {"bnf_code": "0203020C0BCAAAA"},
            {"bnf_code": "1106000X0AAA4A4"},
        ]
    )
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    ingest_build_analysis_bnf_data()

    page.goto(live_server.url + "/analysis/build2/")

    # The page loads with no active filters and the numerator tab selected.
    numerator_panel = panel_for_prefix(page, "ntr")
    denominator_panel = panel_for_prefix(page, "dtr")
    numerator_tab = page.get_by_role("tab", name="Numerator")
    denominator_tab = page.get_by_role("tab", name="Denominator")

    expect(numerator_tab).to_have_attribute("aria-selected", "true")
    expect(dropdown_rows(numerator_panel)).to_have_count(0)
    expect(dropdown_rows(denominator_panel)).to_have_count(0)
    assert add_filter_option_labels(numerator_panel) == [
        "Choose a filter...",
        "Ingredient",
        "VTM",
        "BNF hierarchy",
        "Form/route",
    ]
    expect(results_counts(numerator_panel)).to_be_hidden()
    expect(results_table(numerator_panel)).to_be_hidden()

    # BNF options are populated dynamically and searchable by code prefix.
    add_filter(numerator_panel, "BNF hierarchy")
    expect(dropdown_body(numerator_panel, "BNF hierarchy")).to_be_visible()
    expect(
        dropdown_option_elements(numerator_panel, "BNF hierarchy").first
    ).to_be_visible()
    assert dropdown_option_texts(numerator_panel, "BNF hierarchy")[:4] == [
        "Anaesthesia (Chapter)",
        "Cardiovascular System (Chapter)",
        "Endocrine System (Chapter)",
        "Eye (Chapter)",
    ]
    dropdown_input(numerator_panel, "BNF hierarchy").fill("1106000X0")
    expect(
        dropdown_option_elements(numerator_panel, "BNF hierarchy").filter(
            has_text="Pilocarpine (Chemical)"
        )
    ).to_be_visible()
    remove_dropdown_button(numerator_panel, "BNF hierarchy").click()

    # Selecting multiple VTM values updates the numerator query and URL.
    add_filter(numerator_panel, "VTM")
    expect(dropdown_body(numerator_panel, "VTM")).to_be_visible()
    select_suggestion(numerator_panel, "VTM", "Aden", "Adenosine")
    select_suggestion(numerator_panel, "VTM", "Pilo", "Pilocarpine")

    assert "Ingredient (excluded)" in add_filter_option_labels(numerator_panel)
    assert "VTM (excluded)" in add_filter_option_labels(numerator_panel)

    expect(page).to_have_url(
        live_server.url + "/analysis/build2/?ntr_vtm=108502004%2C90356005"
    )
    expect(results_counts(numerator_panel)).to_have_text(
        "4 dm+d products (2 VMPs, 2 AMPs)"
    )
    expect(results_empty(numerator_panel)).to_be_hidden()
    expect(results_table(numerator_panel)).to_be_visible()
    expect(vtm_row(numerator_panel)).to_have_attribute("data-status", STATUS_INCLUDED)
    expect(vmp_row(numerator_panel)).to_have_attribute("data-status", STATUS_INCLUDED)
    expect(pilocarpine_vtm_row(numerator_panel)).to_have_attribute(
        "data-status", STATUS_INCLUDED
    )

    # Adding an ingredient narrows the results while preserving the VTM summary.
    add_filter(numerator_panel, "Ingredient")
    expect(dropdown_body(numerator_panel, "VTM")).to_be_hidden()
    expect(dropdown_body(numerator_panel, "Ingredient")).to_be_visible()
    select_suggestion(numerator_panel, "Ingredient", "Aden", "Adenosine")

    expect(results_counts(numerator_panel)).to_have_text(
        "2 dm+d products (1 VMPs, 1 AMPs)"
    )
    expect(results_empty(numerator_panel)).to_be_hidden()
    expect(results_table(numerator_panel)).to_be_visible()
    expect(page).to_have_url(
        live_server.url
        + "/analysis/build2/?ntr_vtm=108502004%2C90356005&ntr_ingredient=35431001"
    )
    expect(dropdown_summary(numerator_panel, "VTM")).to_contain_text("Adenosine")
    expect(dropdown_summary(numerator_panel, "VTM")).to_contain_text("Pilocarpine")

    # Reopening VTM shows only the values still possible under the other filters.
    toggle_dropdown_button(numerator_panel, "VTM").click()
    expect(dropdown_body(numerator_panel, "VTM")).to_be_visible()
    expect(dropdown_body(numerator_panel, "Ingredient")).to_be_hidden()
    assert dropdown_option_texts(numerator_panel, "VTM") == [
        "Adenosine",
        "Pilocarpine",
    ]

    # Include and exclude form/route filters narrow each other and can produce no matches.
    add_filter(numerator_panel, "Form/route")
    expect(dropdown_body(numerator_panel, "Form/route")).to_be_visible()
    assert dropdown_option_texts(numerator_panel, "Form/route") == [
        "solutioninjection.intravenous"
    ]
    select_suggestion(
        numerator_panel,
        "Form/route",
        "intravenous",
        "solutioninjection.intravenous",
    )

    add_filter(numerator_panel, "Form/route (excluded)")
    expect(dropdown_body(numerator_panel, "Form/route (excluded)")).to_be_visible()
    assert selected_dropdown_option_labels(numerator_panel, "Form/route") == [
        "solutioninjection.intravenous"
    ]
    assert dropdown_option_texts(numerator_panel, "Form/route (excluded)") == [
        "solutioninjection.intravenous"
    ]
    select_suggestion(
        numerator_panel,
        "Form/route (excluded)",
        "intravenous",
        "solutioninjection.intravenous",
    )
    assert selected_dropdown_option_labels(
        numerator_panel,
        "Form/route (excluded)",
    ) == ["solutioninjection.intravenous"]
    expect(results_empty(numerator_panel)).to_be_visible()

    # Showing non-matching rows exposes excluded statuses in the results table.
    show_only_matching_checkbox(numerator_panel).uncheck()
    expect(results_table(numerator_panel)).to_be_visible()
    expect(vtm_row(numerator_panel)).to_have_attribute("data-status", STATUS_EXCLUDED)
    expect(vmp_row(numerator_panel)).to_have_attribute("data-status", STATUS_EXCLUDED)
    toggle_dropdown_button(numerator_panel, "VTM").click()
    assert dropdown_option_texts(numerator_panel, "VTM") == [
        "Adenosine",
        "Pilocarpine",
    ]

    # Removing narrowing filters restores broader availability and resets the URL.
    remove_dropdown_button(numerator_panel, "Form/route (excluded)").click()
    remove_dropdown_button(numerator_panel, "Form/route").click()
    expect(dropdown_summary(numerator_panel, "VTM")).to_contain_text("Adenosine")
    expect(dropdown_summary(numerator_panel, "VTM")).to_contain_text("Pilocarpine")
    remove_dropdown_button(numerator_panel, "Ingredient").click()
    assert dropdown_option_texts(numerator_panel, "VTM")[:2] == [
        "Adenosine",
        "Pilocarpine",
    ]
    show_only_matching_checkbox(numerator_panel).check()
    add_filter(numerator_panel, "BNF hierarchy")
    remove_dropdown_button(numerator_panel, "BNF hierarchy").click()

    expect(page).to_have_url(
        live_server.url + "/analysis/build2/?ntr_vtm=108502004%2C90356005"
    )
    assert "BNF hierarchy" in add_filter_option_labels(numerator_panel)

    # Removing the final numerator filter returns the panel to its prompt state.
    remove_dropdown_button(numerator_panel, "VTM").click()

    expect(page).to_have_url(live_server.url + "/analysis/build2/")
    expect(dropdown_rows(numerator_panel)).to_have_count(0)
    expect(results_counts(numerator_panel)).to_be_hidden()
    expect(results_table(numerator_panel)).to_be_hidden()
    expect(results_prompt(numerator_panel)).to_be_visible()

    # Denominator filters operate independently from numerator filters and URL state.
    denominator_tab.click()
    expect(denominator_tab).to_have_attribute("aria-selected", "true")

    add_filter(denominator_panel, "Ingredient")
    select_suggestion(denominator_panel, "Ingredient", "Aden", "Adenosine")
    add_filter(denominator_panel, "Ingredient (excluded)")
    select_suggestion(
        denominator_panel,
        "Ingredient (excluded)",
        "Aden",
        "Adenosine",
    )

    expect(page).to_have_url(
        live_server.url
        + "/analysis/build2/?dtr_ingredient=35431001&dtr_ingredient_exclude=35431001"
    )
    expect(results_counts(denominator_panel)).to_have_text(
        "0 dm+d products (0 VMPs, 0 AMPs)"
    )
    expect(results_empty(denominator_panel)).to_be_visible()
    expect(results_table(denominator_panel)).to_be_hidden()

    # The denominator table can still show excluded rows when requested.
    show_only_matching_checkbox(denominator_panel).uncheck()
    expect(results_table(denominator_panel)).to_be_visible()
    expect(vtm_row(denominator_panel)).to_have_attribute("data-status", STATUS_EXCLUDED)
    expect(vmp_row(denominator_panel)).to_have_attribute("data-status", STATUS_EXCLUDED)
    expect(vmp_name(denominator_panel)).to_have_css(
        "text-decoration-line",
        "line-through",
    )


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_build_analyse_loads_dynamic_filters_from_url(
    live_server, page, rxdb, settings, tmp_path
):
    # Seed the same small dataset used by the main interaction test.
    rxdb.ingest(
        [
            {"bnf_code": "0203020C0BBAAAA"},
            {"bnf_code": "0203020C0BCAAAA"},
            {"bnf_code": "1106000X0AAA4A4"},
        ]
    )
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)

    page.goto(
        live_server.url
        + "/analysis/build2/?ntr_vtm=108502004,90356005&ntr_form_route=24"
        + "&dtr_ingredient=35431001&dtr_ingredient_exclude=35431001"
    )

    numerator_panel = panel_for_prefix(page, "ntr")
    denominator_panel = panel_for_prefix(page, "dtr")
    denominator_tab = page.get_by_role("tab", name="Denominator")

    # Numerator filters and results are restored from the query string on load.
    expect(dropdown_rows(numerator_panel)).to_have_count(2)
    expect(dropdown_body(numerator_panel, "VTM")).to_be_hidden()
    expect(dropdown_body(numerator_panel, "Form/route")).to_be_hidden()
    assert selected_dropdown_option_labels(numerator_panel, "VTM") == [
        "Adenosine",
        "Pilocarpine",
    ]
    assert selected_dropdown_option_labels(numerator_panel, "Form/route") == [
        "solutioninjection.intravenous"
    ]
    expect(dropdown_summary(numerator_panel, "Form/route")).to_contain_text(
        "solutioninjection.intravenous"
    )
    expect(show_only_matching_checkbox(numerator_panel)).to_be_checked()
    expect(results_counts(numerator_panel)).to_have_text(
        "2 dm+d products (1 VMPs, 1 AMPs)"
    )
    expect(results_empty(numerator_panel)).to_be_hidden()
    expect(results_table(numerator_panel)).to_be_visible()

    # Denominator filters are restored independently from the same URL.
    expect(dropdown_rows(denominator_panel)).to_have_count(2)
    assert selected_dropdown_option_labels(denominator_panel, "Ingredient") == [
        "Adenosine"
    ]
    assert selected_dropdown_option_labels(
        denominator_panel, "Ingredient (excluded)"
    ) == ["Adenosine"]
    expect(show_only_matching_checkbox(denominator_panel)).to_be_checked()
    expect(results_counts(denominator_panel)).to_have_text(
        "0 dm+d products (0 VMPs, 0 AMPs)"
    )

    # Switching tabs preserves the restored denominator empty state.
    denominator_tab.click()
    expect(results_empty(denominator_panel)).to_be_visible()
    expect(results_table(denominator_panel)).to_be_hidden()


def panel_for_prefix(page, prefix):
    """Return the query panel with the given prefix."""
    return page.locator(f'[data-query-panel][data-panel-prefix="{prefix}"]')


def ingest_build_analysis_bnf_data():
    """Seed BNF codes used by the build-analysis tests."""
    for level, code, name in [
        [1, "02", "Cardiovascular System"],
        [1, "06", "Endocrine System"],
        [1, "11", "Eye"],
        [1, "15", "Anaesthesia"],
        [2, "0203", "Paroxysmal supraventricular tachycardias"],
        [5, "0203020C0", "Adenosine"],
        [2, "1106", "Glaucoma and ocular hypertension"],
        [5, "1106000X0", "Pilocarpine"],
    ]:
        BNFCode.objects.create(code=code, name=name, level=level)


def add_filter(panel, label):
    """Add a filter to the panel via the Add filter select."""
    add_filter_select(panel).select_option(label=label)


def add_filter_select(panel):
    """Return the Add filter select element."""
    return panel.locator("[data-add-filter]")


def add_filter_option_labels(panel):
    """Return the labels of every option in the Add filter select."""
    return (
        add_filter_select(panel)
        .locator("option")
        .evaluate_all("(options) => options.map((option) => option.textContent)")
    )


def dropdown_rows(panel):
    """Return every dropdown currently mounted in the panel."""
    return panel.locator("[data-dropdown]")


def dropdown_row(panel, label):
    """Return the dropdown whose header matches the given label."""
    return panel.locator("[data-dropdown]").filter(has_text=label).first


def dropdown_input(panel, label):
    """Return the search input inside the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-input]")


def dropdown_options(panel, label):
    """Return the options select inside the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-options]")


def dropdown_option_elements(panel, label):
    """Return every <option> inside the labelled dropdown."""
    return dropdown_options(panel, label).locator("option")


def dropdown_option_texts(panel, label):
    """Return the text of every option in the labelled dropdown."""
    return dropdown_option_elements(panel, label).evaluate_all(
        "(options) => options.map((option) => option.textContent)"
    )


def dropdown_body(panel, label):
    """Return the expanded body of the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-body]")


def dropdown_summary(panel, label):
    """Return the collapsed summary of the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-summary]")


def clear_dropdown_search(panel, label):
    """Return the Clear button for the labelled dropdown's search."""
    return dropdown_row(panel, label).locator("[data-clear-search]")


def selected_dropdown_option_labels(panel, label):
    """Return the labels of the currently selected options."""
    return (
        dropdown_options(panel, label)
        .locator("option:checked")
        .evaluate_all("(options) => options.map((option) => option.textContent)")
    )


def remove_dropdown_button(panel, label):
    """Return the close button that removes the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-remove]")


def toggle_dropdown_button(panel, label):
    """Return the caret button that opens/closes the labelled dropdown."""
    return dropdown_row(panel, label).locator("[data-dropdown-toggle]")


def show_only_matching_checkbox(panel):
    """Return the 'Show only matching' checkbox."""
    return panel.locator("[data-show-only-matching]")


def results_prompt(panel):
    """Return the prompt shown before any query runs."""
    return panel.locator("[data-results-prompt]")


def results_counts(panel):
    """Return the results-counts summary line."""
    return panel.locator("[data-results-counts]")


def results_empty(panel):
    """Return the 'No medications matched' notice."""
    return panel.locator("[data-results-empty]")


def results_table(panel):
    """Return the results table."""
    return panel.locator("[data-results-table]")


def vtm_row(panel):
    """Return the Adenosine VTM row."""
    return row_for_text(panel, "Adenosine")


def vmp_row(panel):
    """Return the Adenosine VMP row."""
    return row_for_text(panel, "Adenosine 6mg/2ml solution for injection vials")


def vmp_name(panel):
    """Return the name cell of the Adenosine VMP row."""
    return vmp_row(panel).locator("[data-name]")


def pilocarpine_vtm_row(panel):
    """Return the Pilocarpine VTM row."""
    return row_for_text(panel, "Pilocarpine")


def pilocarpine_vmp_row(panel):
    """Return the Pilocarpine VMP row."""
    return row_for_text(
        panel, "Pilocarpine hydrochloride 6% eye drops preservative free"
    )


def row_for_text(panel, text):
    """Return the <tr> containing the given exact text."""
    return panel.get_by_text(text, exact=True).locator("xpath=ancestor::tr[1]")


def select_suggestion(panel, label, search_text, suggestion_text):
    """Search within a dropdown and add a matching option to its selection."""
    dropdown_input(panel, label).fill(search_text)
    existing = selected_dropdown_option_labels(panel, label)
    dropdown_options(panel, label).select_option(label=[*existing, suggestion_text])
