"""python manage.py live_worker <role>: start a Celery process, or idle during a database rollback.

The live host runs this as the worker/beat container command. While deploy/rollback.json is in the commit (a
database rollback's first step, when nothing may write) the process idles instead of starting Celery. One
command with no shell branching, for the same reason as live_deploy: the host wraps the container command in
its own shell, which mangles an inline `if ... fi`.
"""
import os
import time

from django.core.management.base import BaseCommand

from apps.core.health import load_rollback

ROLES = {
    'worker': ['celery', '-A', 'config', 'worker', '--loglevel', 'info', '--concurrency', '2'],
    'beat': ['celery', '-A', 'config', 'beat', '--loglevel', 'info'],
}


class Command(BaseCommand):
    help = 'Run a Celery worker or beat, idling while a database rollback is under way.'

    def add_arguments(self, parser):
        parser.add_argument('role', choices=sorted(ROLES))

    def handle(self, *args, **options):
        if load_rollback() is not None:
            self.stdout.write('database rollback: idle')
            while True:
                time.sleep(3600)
        argv = ROLES[options['role']]
        os.execvp(argv[0], argv)  # replace this process with Celery so signals reach it directly
