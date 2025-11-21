import pytest

from openprescribing.data.models import Org


@pytest.mark.django_db(databases=["data"])
def test_relation_fields():
    # This looks a bit like we're testing Django here, but the model field configuration
    # which makes this all work is not entirely trivial so it's worth confirming that
    # we've got it right
    parent_1 = Org.objects.create(id="p1", org_type=Org.OrgType.REGION)
    parent_2 = Org.objects.create(id="p2", org_type=Org.OrgType.REGION)

    child_1 = Org.objects.create(id="c1", org_type=Org.OrgType.PRACTICE)
    child_1.parents.set([parent_1, parent_2])

    child_2 = Org.objects.create(id="c2", org_type=Org.OrgType.PRACTICE)
    child_2.parents.set([parent_1])

    assert set(parent_1.children.all()) == {child_1, child_2}
    assert set(parent_2.children.all()) == {child_1}

    assert set(child_1.parents.all()) == {parent_1, parent_2}
    assert set(child_2.parents.all()) == {parent_1}


def test_org_repr():
    org = Org(id="ABC123", name="North Road Surgery", org_type=Org.OrgType.PRACTICE)
    assert repr(org) == "Org('ABC123', Org.OrgType.PRACTICE, 'North Road Surgery')"


@pytest.mark.django_db(databases=["data"])
def test_as_practice_code_map():
    for icb_i in range(2):
        icb = Org.objects.create(id=f"icb{icb_i}", org_type=Org.OrgType.ICB)
        for pcn_i in range(2):
            pcn = Org.objects.create(id=f"pcn{icb_i}{pcn_i}", org_type=Org.OrgType.PCN)
            pcn.parents.add(icb)
        for pra_i in range(3):
            pra = Org.objects.create(
                id=f"pra{icb_i}{pra_i}", org_type=Org.OrgType.PRACTICE
            )
            pra.parents.add(icb)

    result = Org.objects.filter(org_type=Org.OrgType.ICB).with_practice_ids()

    assert result == (
        (
            Org.objects.get(id="icb0"),
            {"pra00", "pra01", "pra02"},
        ),
        (
            Org.objects.get(id="icb1"),
            {"pra10", "pra11", "pra12"},
        ),
    )


@pytest.mark.django_db(databases=["data"])
def test_as_practice_code_map_only_uses_direct_relations():
    region = Org.objects.create(id="r", org_type=Org.OrgType.REGION)
    icb = Org.objects.create(id="i", org_type=Org.OrgType.ICB)
    practice = Org.objects.create(id="p", org_type=Org.OrgType.PRACTICE)

    icb.parents.add(region)
    practice.parents.add(icb)

    assert Org.objects.filter(id="r").with_practice_ids() == (
        (
            region,
            frozenset(),
        ),
    )


@pytest.mark.django_db(databases=["data"])
def test_as_practice_code_map_treats_practices_as_their_own_descendants():
    practices = [
        Org.objects.create(id=f"pra{i}", org_type=Org.OrgType.PRACTICE)
        for i in range(3)
    ]

    assert Org.objects.with_practice_ids() == (
        (practices[0], {"pra0"}),
        (practices[1], {"pra1"}),
        (practices[2], {"pra2"}),
    )


@pytest.mark.django_db(databases=["data"])
def test_as_practice_code_map_handles_empty_querysets():
    assert Org.objects.with_practice_ids() == ()
