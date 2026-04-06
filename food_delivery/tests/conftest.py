import pytest
from django.contrib.auth.models import Group

@pytest.fixture(autouse=True)
def create_groups(db):
    Group.objects.get_or_create(name='Customers')
    Group.objects.get_or_create(name='RestrauntOwners')
    Group.objects.get_or_create(name='Drivers')
    print("groups created for test")
