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
    region = Org.objects.create(id="r", org_type=Org.OrgType.REGION)

    for icb_i in range(3):
        icb = Org.objects.create(id=f"icb{icb_i}", org_type=Org.OrgType.ICB)
        icb.parents.add(region)
        for pcn_i in range(3):
            pcn = Org.objects.create(id=f"pcn{icb_i}{pcn_i}", org_type=Org.OrgType.PCN)
            pcn.parents.add(icb)
            for pra_i in range(3):
                pra = Org.objects.create(
                    id=f"pra{icb_i}{pcn_i}{pra_i}", org_type=Org.OrgType.PRACTICE
                )
                pra.parents.add(pcn)

    # Check that we get the right results when selecting a subset of ICBs
    icbs = Org.objects.filter(org_type=Org.OrgType.ICB).exclude(id="icb1")
    results = icbs.with_practice_ids()

    expected = []
    for icb_i in [0, 2]:
        icb = Org.objects.get(id=f"icb{icb_i}")
        practice_ids = frozenset(
            f"pra{icb_i}{pcn_i}{pra_i}" for pcn_i in range(3) for pra_i in range(3)
        )
        expected.append((icb, practice_ids))

    assert set(results) == set(expected)

    # Check that we get the right results for the entire region
    region_results = Org.objects.filter(id="r").with_practice_ids()

    region_expected = [
        (
            region,
            frozenset(
                f"pra{icb_i}{pcn_i}{pra_i}"
                for icb_i in range(3)
                for pcn_i in range(3)
                for pra_i in range(3)
            ),
        )
    ]

    assert set(region_results) == set(region_expected)

    # Check that empty results sets work without error
    assert Org.objects.filter(id="MISSING").with_practice_ids() == ()

    # Check that practices get mapped to themselves
    practices = Org.objects.filter(
        id__startswith="pra00", org_type=Org.OrgType.PRACTICE
    )
    practice_results = practices.with_practice_ids()

    practice_expected = {(p, frozenset([p.id])) for p in practices}
    assert set(practice_results) == practice_expected
