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

# ingredient_ids and vtm_ids are integers (SNOMED ids).
id_tuples = st.lists(st.integers(min_value=0), max_size=4).map(tuple)


@st.composite
def bnf_queries(draw):
    """Build an arbitrary BNFQuery."""

    return BNFQuery(
        bnf_codes=draw(token_tuples),
        bnf_codes_excluded=draw(token_tuples),
        product_type=draw(st.sampled_from(list(ProductType))),
        form_routes=draw(token_tuples),
        form_routes_excluded=draw(token_tuples),
        forms=draw(token_tuples),
        forms_excluded=draw(token_tuples),
        routes=draw(token_tuples),
        routes_excluded=draw(token_tuples),
        ingredient_ids=draw(id_tuples),
        ingredient_ids_excluded=draw(id_tuples),
        vtm_ids=draw(id_tuples),
        vtm_ids_excluded=draw(id_tuples),
    )


@given(query=bnf_queries())
def test_params_round_trip(query):
    assert BNFQuery.from_params("ntr", query.to_params("ntr")) == query


@given(query=bnf_queries())
def test_dict_round_trip(query):
    assert BNFQuery.from_dict(query.to_dict()) == query
