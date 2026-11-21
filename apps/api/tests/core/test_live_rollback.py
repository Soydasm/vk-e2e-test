"""The database rollback's first step: undo to the targets, then serve only /healthz until the platform moves on."""
import json

import pytest
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory

from apps.core import health


@pytest.mark.django_db
def test_without_rollback_json_the_command_refuses(monkeypatch, tmp_path):
    monkeypatch.setenv('ROLLBACK_FILE', str(tmp_path / 'absent.json'))
    with pytest.raises(Exception):
        call_command('live_rollback')


@pytest.mark.django_db
def test_with_rollback_json_only_healthz_answers(monkeypatch, tmp_path):
    path = tmp_path / 'deploy' / 'rollback.json'
    path.parent.mkdir()
    heads = health.migration_heads(['users'])
    path.write_text(json.dumps({'to_version': 'v0.1.0', 'targets': heads, 'ops': []}))
    monkeypatch.setenv('ROLLBACK_FILE', str(path))
    call_command('live_rollback')          # already there: nothing to undo
    app = health.HealthzMiddleware(lambda request: HttpResponse('app'))
    page = app(RequestFactory().get('/api/v1/hello/'))
    assert page.status_code == 503
    body = json.loads(app(RequestFactory().get('/healthz')).content)
    assert body['rollback'] == 'done' and body['migrations'] == heads
