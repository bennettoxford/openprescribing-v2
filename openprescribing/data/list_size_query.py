from dataclasses import dataclass


@dataclass(frozen=True)
class ListSizeQuery:
    """Represents a query returning list size data."""

    def to_sql(self):
        """Return SQL that returns practice list sizes.

        The query returns one row for each practice for each month with data.
        """

        return "SELECT practice_id, date_id, total AS value FROM list_size"

    def to_params(self, field):
        """Serialize to URL query parameters.

        This is intentionally blank!
        """

        return {}

    def describe(self):
        return {"text": "1000 patients"}
