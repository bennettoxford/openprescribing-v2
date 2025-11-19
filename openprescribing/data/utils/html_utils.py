import dataclasses
import datetime
import re

import bs4


@dataclasses.dataclass
class Resource:
    url: str
    date: datetime.date
    published_date: datetime.date


def parse_nhsd_callout_boxes(html, heading_re):
    doc = bs4.BeautifulSoup(html, "html5lib")
    for heading in doc.select(".callout-box__content-heading"):
        if not re.search(heading_re, heading.text):
            continue
        date_str = re.search(r"(\w+ \d\d\d\d)", heading.text).group(1)
        date = parse_date(f"1 {date_str}")
        published_date_str = (
            heading.find_parent("div", ["callout-box"])
            .select_one(".callout-box__content-description-date")
            .text.replace("Published:", "")
            .strip()
        )
        published_date = parse_date(published_date_str)
        url = heading.find("a")["href"]
        yield Resource(url=url, date=date, published_date=published_date)


def parse_date(date_str):
    try:
        # Parses dates like "1 January 2020"
        return datetime.datetime.strptime(date_str, "%d %B %Y").date()
    except ValueError:
        # Parses dates like "1 Jan 2020"
        return datetime.datetime.strptime(date_str, "%d %b %Y").date()


def find_url(html, *url_regexes):
    doc = bs4.BeautifulSoup(html, "html5lib")
    for url_re in url_regexes:
        matcher = re.compile(url_re)
        matches = {a["href"] for a in doc.find_all("a", href=matcher)}
        assert len(matches) <= 1, f"Ambiguous matches for {url_re!r}: {matches}"
        if len(matches) == 1:
            return list(matches)[0]
    assert False, f"No matches for patterns: {url_regexes}"
