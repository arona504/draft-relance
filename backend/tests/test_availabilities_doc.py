import pytest

pytestmark = pytest.mark.skip(reason="Requires live Keycloak token and seeded data; see README for manual steps")


def test_get_availabilities_example():
    """Document the manual flow for exercising the /queries/scheduling/availabilities endpoint."""
    assert True, "Run curl with a bearer token issued by Keycloak as described in the docs."
