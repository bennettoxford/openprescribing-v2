from datetime import date

import pytest

from openprescribing.data.utils import html_utils


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en" class="no-js">
  <head>
    <title>Patients Registered at a GP Practice - NHS England Digital</title>
  </head>
  <body>
    <div class="article-section" id="past-publications">
      <h2>Past publications</h2>
      <ul class="list list--reset cta-list" data-uipath="ps.series.publications-list.previous">
        <li>
          <div class="callout-box callout-box--grey" role="complementary">
            <div class="callout-box__icon-wrapper">
            </div>
            <div class="callout-box__content callout-box__content--narrow">
              <div class="callout-box__content-heading callout-box__content-heading--light callout-box__content--narrow-heading">
                <h3 itemprop="name">
                  <a href="{url}" class="cta__button" onclick="Series" onkeyup="return vjsu.onKeyUp(event)" itemprop="url">
                    {title} {date}
                  </a>
                </h3>
              </div>
              <div class="callout-box__content-description">
                <div class="rich-text-content">
                  Lorem Ipsum ...
                </div>
                <div class="clearfix">
                  <p class="callout-box__content-description-date">{publication_date}</p>
                </div>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </body>
</html>
"""


def test_parse_nhsd_callout_boxes():
    html = HTML_TEMPLATE.format(
        title="Patients Registered at a GP Practice",
        date="October 2025",
        publication_date="16 October 2025",
        url="/statistical/patients-registered-at-a-gp-practice/october-2025",
    )
    resources = html_utils.parse_nhsd_callout_boxes(
        html,
        r"Registered .* GP Practice",
    )
    assert [(r.date, r.published_date, r.url) for r in resources] == [
        (
            date(2025, 10, 1),
            date(2025, 10, 16),
            "/statistical/patients-registered-at-a-gp-practice/october-2025",
        ),
    ]

    assert list(html_utils.parse_nhsd_callout_boxes(html, r"NO_MATCH")) == []


def test_parse_date():
    assert html_utils.parse_date("10 Feb 2024") == date(2024, 2, 10)
    assert html_utils.parse_date("6 July 2025") == date(2025, 7, 6)
    with pytest.raises(ValueError):
        html_utils.parse_date("2020-01-01")


def test_find_url():
    html = """\
    <a href="/foo/1/bar/"></a>
    <a href="/foo/2/baz/"></a>
    """

    assert html_utils.find_url(html, "/1/") == "/foo/1/bar/"
    assert html_utils.find_url(html, "4", "3", "2") == "/foo/2/baz/"

    with pytest.raises(AssertionError, match="Ambiguous"):
        html_utils.find_url(html, "/foo/")

    with pytest.raises(AssertionError, match="No matches"):
        html_utils.find_url(html, "wat")
