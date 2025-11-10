import datetime
import re
import secrets
from collections import defaultdict


def get_latest_files_by_date(filenames):
    """
    Given a list of filenames of the format:

        <some_word_characters>_YYYY-MM-DD_<any_characters>

    Group them by their date and, for each date, find the lexically greatest file.
    """
    grouped = defaultdict(list)
    for filename in filenames:
        # Ignore hidden files
        if filename.name.startswith("."):
            continue
        match = re.match(r"\w+_(\d{4}-\d{2}-\d{2})_", filename.name)
        assert match, f"Expecting a filename containing an ISO date: {filename}"
        date = datetime.date.fromisoformat(match.group(1))
        grouped[date].append(filename)
    return {date: max(files) for date, files in grouped.items()}


def get_temp_filename_for(filename):
    """
    Support atomically updating `filename` by returning a temporary alternative name

    The intention is not to delete this file after use but to atomically rename it to
    `filename` after we've finished building it. This means that the default behaviour
    of `tempfile` is unhelpful here so we do our own thing. We can also ensure that the
    temporary file is on the same filesystem as its target, which we need to allow for
    atomic renames.
    """
    return filename.with_name(f".{filename.name}.{secrets.token_hex(16)}.tmp")
