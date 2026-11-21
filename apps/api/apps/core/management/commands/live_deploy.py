"""python manage.py live_deploy: the live host's pre-deploy step.

Migrate the database forward before the new version takes traffic — unless VibeKaizen has put
deploy/rollback.json in the commit (a database rollback's first step), when it undoes the newer migrations
instead (delegates to live_rollback). One command with no shell branching: the live host (Render) runs the
pre-deploy command through its own shell, which read an inline `if ... fi` as a single command name and exited
127. A plain executable survives any wrapping.

On the very first deploy the managed database is often still starting when this pre-deploy step runs, so the
first connection is refused ("Connection refused" / "the database system is starting up"). Wait for it to
accept connections (up to ~2 minutes) before migrating, instead of crashing the deploy.
"""
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import OperationalError, connection, connections

from apps.core.health import load_rollback

DB_WAIT_SECONDS = 120
DB_WAIT_INTERVAL = 3


class Command(BaseCommand):
    help = 'Migrate forward, or undo the database when deploy/rollback.json is present (pre-deploy step).'

    def wait_for_database(self):
        deadline = time.monotonic() + DB_WAIT_SECONDS
        while True:
            try:
                connection.close()
                connections['default'].ensure_connection()
                return
            except OperationalError as exc:
                if time.monotonic() >= deadline:
                    raise
                self.stdout.write(f'database not ready yet ({exc}); retrying in {DB_WAIT_INTERVAL}s')
                time.sleep(DB_WAIT_INTERVAL)

    def handle(self, *args, **options):
        self.wait_for_database()
        if load_rollback() is not None:
            call_command('live_rollback')
        else:
            call_command('migrate', '--noinput')
