# pytest-django reads DJANGO_SETTINGS_MODULE from pytest.ini and sets up
# Django automatically. Keep this file so pytest treats the repo root as
# a conftest scope.
import pytest


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Every test starts with an empty cache. Throttle counters (DRF keeps them in the cache) and cached
    values otherwise carry over from one test to the next: the eleventh sign-in of a run answers 429."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()
