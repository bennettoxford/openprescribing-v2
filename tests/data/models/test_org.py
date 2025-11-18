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
