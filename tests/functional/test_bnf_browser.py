import pytest
from playwright.sync_api import expect

from openprescribing.data.models import BNFCode


pytestmark = pytest.mark.functional


@pytest.mark.django_db(databases=["data"])
def test_bnf_browser(live_server, page, sample_data):
    page.goto(live_server.url)
    page.get_by_role("link", name="BNF browser").click()

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
    with page.expect_popup() as glucose_blood_popup:
        page.get_by_text("0601060D0 Glucose blood").click()
    glucose_blood_page = glucose_blood_popup.value
    for bnf_code in BNFCode.objects.filter(code__startswith="0601060D0"):
        expect(
            glucose_blood_page.get_by_text(bnf_code.code, exact=True)
        ).to_be_visible()

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
    with page.expect_popup() as methotrexate_popup:
        page.get_by_text("1001030U0 Methotrexate").click()
    methotrexate_page = methotrexate_popup.value
    for bnf_code in BNFCode.objects.filter(code__startswith="1001030U0"):
        expect(methotrexate_page.get_by_text(bnf_code.code, exact=True)).to_be_visible()
