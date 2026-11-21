"""/healthz is answered before host validation and the HTTPS redirect, and never shows an error's text."""
import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from apps.core.health import HealthzMiddleware


def _never(request):
    return HttpResponse('the app', status=418)


@pytest.mark.django_db
@pytest.mark.parametrize('path', ['/healthz', '/healthz/'])
def test_healthz_answers_with_any_host(path):
    request = RequestFactory().get(path, HTTP_HOST='10.0.0.7:8000')  # not an allowed host
    response = HealthzMiddleware(_never)(request)
    assert response.status_code == 200
    assert b'"status": "ok"' in response.content


def test_other_paths_go_to_the_app():
    response = HealthzMiddleware(_never)(RequestFactory().get('/api/v1/hello/'))
    assert response.status_code == 418


def test_a_database_failure_is_degraded_without_details(monkeypatch):
    from apps.core import health

    class Broken:
        def cursor(self):
            raise RuntimeError('password authentication failed for user "secret_user"')

    monkeypatch.setattr(health, 'connection', Broken())
    response = HealthzMiddleware(_never)(RequestFactory().get('/healthz'))
    assert response.status_code == 503
    assert b'degraded' in response.content and b'secret_user' not in response.content
