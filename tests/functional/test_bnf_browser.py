import pytest
from playwright.sync_api import expect

from openprescribing.data.models import BNFCode


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_bnf_browser(live_server, page, sample_data):
    page.goto(live_server.url + "/bnf/")

    modal = page.locator("#bnf-table-modal")
    modal_body = page.locator("#bnf-table-modal .modal-body")

    # Test that clicking on nodes expands them.
    expect(page.get_by_text("Drugs used in diabetes")).not_to_be_visible()
    page.get_by_text("Endocrine System").click()

    # Test clicking on the name.
    page.get_by_text("Drugs used in diabetes").click()

    # Test clicking on the code.
    page.get_by_text("060106", exact=True).click()

    # Test clicking on the span.
    page.get_by_text("0601060  Diabetic diagnostic and monitoring agents").click()

    # Test that the codes for a chemical substance (without generics) and its products
    # and presentations are visible.
    page.get_by_text("0601060D0 Glucose blood").click()
    expect(modal).to_be_visible()
    for bnf_code in BNFCode.objects.filter(code__startswith="0601060D0").exclude(
        code="0601060D0"
    ):
        expect(modal_body.get_by_text(bnf_code.code, exact=True)).to_be_visible()
    modal.get_by_role("button").click()
    expect(modal).not_to_be_visible()

    # Test that clicking on an expanded node hides its descendants.
    expect(page.get_by_text("Drugs used in diabetes")).to_be_visible()
    page.get_by_text("Endocrine System").click()
    expect(page.get_by_text("Drugs used in diabetes")).not_to_be_visible()

    # Test search behaviour.
    expect(page.get_by_text("Methotrexate")).not_to_be_visible()
    page.get_by_role("textbox", name="Search by name or code").click()
    page.get_by_role("textbox", name="Search by name or code").fill("methotrexate")
    page.get_by_role("button", name="Search").click()
    expect(page.get_by_text("Methotrexate")).to_be_visible()
    expect(page.get_by_text("1001030U0 Methotrexate")).to_have_css(
        "background-color", "rgba(255, 255, 0, 0.2)"
    )
    expect(
        page.get_by_text("1001030  Rheumatic disease suppressant drugs")
    ).to_have_css("background-color", "rgba(0, 0, 0, 0)")

    # Test that the codes for the chemical substance and its products and presentations
    # are visible.
    page.get_by_text("1001030U0 Methotrexate").click()
    expect(modal).to_be_visible()
    for bnf_code in BNFCode.objects.filter(code__startswith="1001030U0").exclude(
        code="1001030U0"
    ):
        expect(modal_body.get_by_text(bnf_code.code, exact=True)).to_be_visible()
    modal.get_by_role("button").click()
    expect(modal).not_to_be_visible()
