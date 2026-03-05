from ..bnf_query import BNFQuery


def search(terms, product_type):
    """Return the BNF presentation codes (as strings) that match the given query.

    A query is a list of terms (as strings) and a product type.

    A term is either:

    * any BNF code. All BNF presentation codes that are descendants of this
      BNF code are matched; or

    * a BNF chemical substance code (nine-characters), an underscore, and
      a strength and formulation part (two-characters). The underscore is a
      wild card that replaces the product part (two-characters). All
      BNF presentation codes that are descendants of this BNF chemical substance code,
      and have this strength and formulation part, are matched. For example,
      "040702040_AM" matches "040702040AAAMAM", which is the BNF presentation code for
      "Tramadol 300mg modified-release tablets".

    A product type filters the matched BNF presentation codes to generic, branded,
    or all products.
    """

    query = BNFQuery.build(terms, product_type)
    return query.get_matching_presentation_codes()


def describe_search(terms, product_type):
    """Return dictionary describing the query.

    See docstring of search() for description of query.
    """

    query = BNFQuery.build(terms, product_type)
    return query.describe()
