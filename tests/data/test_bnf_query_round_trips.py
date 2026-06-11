import string

from hypothesis import given
from hypothesis import strategies as st

from openprescribing.data.bnf_query import (
    BNFQuery,
    ProductType,
)


# Tokens used to build arbitrary id/code values. They must be non-empty (an empty
# tuple is omitted by the serializers and reconstructed as an empty tuple, but a tuple
# containing an empty string is not) and must not contain commas (the separator used by
# to_params/from_params).
tokens = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=8)
token_tuples = st.lists(tokens, max_size=4).map(tuple)


@st.composite
def bnf_queries(draw, *, include_form_routes=True):
    """Build an arbitrary BNFQuery.

    form_route_ids are serialized to descriptions and back via the database by
    to_dict/from_dict, so they can only be included for serializers that round-trip
    them as raw, order-preserving ids (i.e. to_params/from_params).
    """

    return BNFQuery(
        bnf_codes=draw(token_tuples),
        bnf_codes_excluded=draw(token_tuples),
        product_type=draw(st.sampled_from(list(ProductType))),
        form_routes=draw(token_tuples) if include_form_routes else (),
        form_routes_excluded=draw(token_tuples) if include_form_routes else (),
        ingredient_ids=draw(token_tuples),
        ingredient_ids_excluded=draw(token_tuples),
        vtm_ids=draw(token_tuples),
        vtm_ids_excluded=draw(token_tuples),
    )


@given(query=bnf_queries())
def test_params_round_trip(query):
    assert BNFQuery.from_params("ntr", query.to_params("ntr")) == query


@given(query=bnf_queries(include_form_routes=False))
def test_dict_round_trip(query):
    assert BNFQuery.from_dict(query.to_dict()) == query
