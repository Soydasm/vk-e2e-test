"""GET /healthz: is this version up, and can it reach its database?

Asked by Render before a new version takes traffic, by the platform from outside, and by the local rehearsal.
Answered by a middleware at the top of the stack, before host validation, the HTTPS redirect and the URL
router: a health check comes over plain HTTP with whatever Host header the prober uses, and must not be
redirected or refused for that. It says ok or degraded and the release; never an error's text.

Maintenance: a version deployed with deploy/rollback.json is the database rollback's first step (VibeKaizen,
docs/live.md). Its pre-deploy command has undone the newer migrations (`python manage.py live_rollback`); it
serves only /healthz — saying `"rollback": "done"` and each app's last applied migration, read from
django_migrations — and a 503 maintenance page everywhere else, so nothing writes to the database until the
platform moves the live version back.
"""
import json
import logging
import os
from pathlib import Path

from django.db import connection
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

PATHS = frozenset({'/healthz', '/healthz/'})
MAINTENANCE_PAGE = ('<!doctype html><meta charset="utf-8"><title>Maintenance</title>'
                    '<p style="font-family:sans-serif">We are rolling back an update. Please try again in a few '
                    'minutes.</p>')


def _release() -> str:
    return os.environ.get('RELEASE_VERSION') or os.environ.get('RENDER_GIT_COMMIT', '')[:12]


def rollback_file():
    """deploy/rollback.json in the image (/app/deploy) or in a checkout of the repository; None without one."""
    if os.environ.get('ROLLBACK_FILE'):
        path = Path(os.environ['ROLLBACK_FILE'])
        return path if path.is_file() else None
    here = Path(__file__).resolve()
    for root in (here.parents[2], here.parents[4] if len(here.parents) > 4 else here.parents[2]):
        path = root / 'deploy' / 'rollback.json'
        if path.is_file():
            return path
    return None


def load_rollback():
    """The database rollback this version was deployed for ({to_version, targets, ops}), or None."""
    path = rollback_file()
    if path is None:
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def migration_heads(apps) -> dict:
    """{app: its last applied migration, or 'zero'} from django_migrations. Reads nothing else."""
    from django.db.migrations.recorder import MigrationRecorder
    applied = MigrationRecorder(connection).applied_migrations()
    out = {}
    for app in apps:
        names = sorted(name for label, name in applied if label == app)
        out[app] = names[-1] if names else 'zero'
    return out


def health() -> tuple:
    release = _release()
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT 1')
    except Exception:  # noqa: BLE001 - any failure here means "not ready"
        logger.exception('healthz: the database is not reachable')
        return {'status': 'degraded', 'database': 'unavailable', 'release': release}, 503
    return {'status': 'ok', 'database': 'ok', 'release': release}, 200


def rollback_health(plan: dict) -> tuple:
    """/healthz while this version is the database rollback's first step."""
    targets = {str(k): str(v or 'zero') for k, v in (plan.get('targets') or {}).items()}
    if plan.get('unreadable'):
        return {'status': 'ok', 'database': 'ok', 'release': _release(), 'rollback': 'unknown'}, 200
    try:
        heads = migration_heads(targets)
    except Exception:  # noqa: BLE001
        logger.exception('healthz: the migration state is not readable')
        return {'status': 'degraded', 'database': 'unavailable', 'release': _release(), 'rollback': 'unknown'}, 503
    done = all(heads.get(app) == target for app, target in targets.items())
    return {'status': 'ok', 'database': 'ok', 'release': _release(), 'rollback': 'done' if done else 'mismatch',
            'to_version': str(plan.get('to_version') or ''), 'migrations': heads}, 200


class HealthzMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        try:
            self.rollback = load_rollback()
        except (OSError, ValueError):
            logger.exception('deploy/rollback.json is unreadable: serving maintenance only')
            self.rollback = {'unreadable': True}

    def __call__(self, request):
        if request.path_info in PATHS and request.method in ('GET', 'HEAD'):
            body, status = rollback_health(self.rollback) if self.rollback is not None else health()
            return JsonResponse(body, status=status)
        if self.rollback is not None:
            response = HttpResponse(MAINTENANCE_PAGE, status=503, content_type='text/html; charset=utf-8')
            response['Retry-After'] = '120'
            return response
        return self.get_response(request)
