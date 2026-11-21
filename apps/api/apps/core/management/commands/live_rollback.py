"""python manage.py live_rollback: the database half of a rollback, run by the live host's pre-deploy command.

VibeKaizen writes deploy/rollback.json on a commit of the version that is live now — the newer one, because only
its code knows the migrations to undo — and the live host deploys it. render.yaml's preDeployCommand runs this
command instead of `migrate` while that file is there:

    {"to_version": "v1.2.0", "targets": {"<app>": "<its last migration at v1.2.0, or zero>"},
     "ops": ["ops/<name>.rollback.py", ...]}

1. the ops rollback scripts, in the order given (newest first): they undo what was done on the newer schema;
2. the reverse migrations, all targets in one plan, so Django unapplies them in reverse dependency order.

Any failure stops with a non-zero exit, and the live host keeps the previous version running (a failed pre-deploy
command fails the deploy). The version then starts in maintenance (apps/core/health.py) until VibeKaizen deploys
`to_version`. Data written since that version is lost with the columns and tables that are undone; the database's
own backups (Render → the database → Recovery) are the last resort.
"""
import runpy

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.core.health import load_rollback, rollback_file


class Command(BaseCommand):
    help = 'Undo the newer migrations and ops scripts named in deploy/rollback.json (VibeKaizen database rollback).'

    def handle(self, *args, **options):
        plan = load_rollback()
        if plan is None:
            raise CommandError('deploy/rollback.json not found: there is nothing to roll back')
        root = rollback_file().resolve().parent.parent
        targets = [(app, None if name in ('', 'zero', None) else name)
                   for app, name in (plan.get('targets') or {}).items()]
        executor = MigrationExecutor(connection)
        for app, name in targets:
            if name and (app, name) not in executor.loader.graph.nodes:
                raise CommandError(f'{app}.{name} is not a migration of this version')
        steps = executor.migration_plan(targets) if targets else []
        if any(not backwards for _, backwards in steps):
            raise CommandError('the rollback would apply migrations, not undo them: refusing')
        for script in plan.get('ops') or []:
            path = (root / script).resolve()
            if (root / 'ops') not in path.parents or not path.is_file():
                raise CommandError(f'{script}: not an ops rollback script of this version')
            self.stdout.write(f'ops rollback: {script}')
            if path.suffix == '.sql':
                with connection.cursor() as cur:
                    cur.execute(path.read_text(encoding='utf-8'))
            else:
                runpy.run_path(str(path), run_name='__main__')
        for migration, _ in steps:
            self.stdout.write(f'unapply {migration.app_label}.{migration.name}')
        if steps:
            executor.migrate(targets, plan=steps)
        self.stdout.write(self.style.SUCCESS(f"rollback done: the database is at {plan.get('to_version', '?')}"))
