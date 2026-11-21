"""The live-key check: in production the app refuses to start while a live key is missing or wrong.

The names and their rules come from deploy/required-env.json (in the image: /app/required-env.json). What
is reported is a key's name and the rule it breaks, never its value: this output lands in deploy logs.

    VK_SKIP_LIVE_ENV_CHECK=1   skips the check; set only while the image is built (collectstatic)
    REQUIRED_ENV_FILE=<path>   reads the list from somewhere else

The platform writes deploy/required-env.json; it is not edited by hand.
"""
import json
import os
import sys
from pathlib import Path

SKIP = 'VK_SKIP_LIVE_ENV_CHECK'

#: Without the file (an image built before it existed) the minimum every live API needs.
FALLBACK = [
    {'name': 'SECRET_KEY', 'service': 'api',
     'rules': {'must_not_equal': ['dev-secret-not-for-production', 'dev-secret', 'change-me', 'ci-secret']}},
    {'name': 'ALLOWED_HOSTS', 'service': 'api'},
]


def _candidates():
    if os.environ.get('REQUIRED_ENV_FILE'):
        yield Path(os.environ['REQUIRED_ENV_FILE'])
    api_root = Path(__file__).resolve().parent.parent
    yield api_root / 'required-env.json'                        # the image
    yield api_root.parent.parent / 'deploy' / 'required-env.json'  # a checkout of the repository


def load_keys(path=None) -> list:
    """The keys the API needs live: deploy/required-env.json's api entries, or FALLBACK without the file."""
    paths = [Path(path)] if path else list(_candidates())
    for candidate in paths:
        if candidate.is_file():
            data = json.loads(candidate.read_text(encoding='utf-8'))
            return [k for k in data.get('keys', []) if k.get('service', 'api') == 'api']
    return list(FALLBACK)


def problems(keys, environ=None) -> list:
    """One sentence per broken key, naming the key and the rule. Never the value."""
    environ = os.environ if environ is None else environ
    out = []
    for key in keys:
        name = key['name']
        value = environ.get(name, '')
        if not value.strip():
            out.append(f'{name} is not set')
            continue
        rules = key.get('rules') or {}
        if 'min_length' in rules and len(value) < int(rules['min_length']):
            out.append(f"{name} is shorter than {rules['min_length']} characters")
        if value in (rules.get('must_not_equal') or []):
            out.append(f'{name} is a development placeholder, not a live value')
        prefixes = rules.get('must_start_with') or []
        if prefixes and not any(value.startswith(p) for p in prefixes):
            out.append(f"{name} must start with {' or '.join(prefixes)}")
        for prefix in rules.get('must_not_start_with') or []:
            if value.startswith(prefix):
                out.append(f'{name} starts with {prefix}, which is not a live value')
        for part in rules.get('must_not_contain') or []:
            if part in value:
                out.append(f'{name} contains {part}, which is not a live value')
    return out


def enforce(environ=None, path=None):
    """Stop the process, with the names, while the live configuration is incomplete."""
    environ = os.environ if environ is None else environ
    if environ.get(SKIP) == '1':
        return
    found = problems(load_keys(path), environ)
    if not found:
        return
    lines = '\n'.join(f'  - {p}' for p in found)
    sys.stderr.write(
        'The live configuration is incomplete, so the app will not start:\n'
        f'{lines}\n'
        "Set these in the live environment (on Render: the service's Environment page), then deploy again.\n")
    sys.stderr.flush()
    raise SystemExit(78)  # EX_CONFIG
