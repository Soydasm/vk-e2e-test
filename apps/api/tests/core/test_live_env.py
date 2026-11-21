"""The live-key check names what is missing or wrong, never a value, and stops the process."""
import json

import pytest

from config import live_env

KEYS = [
    {'name': 'SECRET_KEY', 'service': 'api', 'rules': {'min_length': 32, 'must_not_equal': ['dev-secret']}},
    {'name': 'DATABASE_URL', 'service': 'api',
     'rules': {'must_start_with': ['postgres://', 'postgresql://'], 'must_not_contain': ['localhost']}},
    {'name': 'STRIPE_SECRET_KEY', 'service': 'api', 'rules': {'must_not_start_with': ['sk_test_']}},
]
GOOD = {'SECRET_KEY': 'x' * 40, 'DATABASE_URL': 'postgres://u:p@db.internal:5432/app',
        'STRIPE_SECRET_KEY': 'sk_live_abc'}


def test_a_complete_live_configuration_passes():
    assert live_env.problems(KEYS, GOOD) == []


def test_missing_and_wrong_keys_are_named_and_values_never_shown():
    env = {'SECRET_KEY': 'dev-secret', 'DATABASE_URL': 'postgres://u:hunter2@localhost:5432/app',
           'STRIPE_SECRET_KEY': 'sk_test_hunter2'}
    found = live_env.problems(KEYS, env)
    text = ' '.join(found)
    assert 'SECRET_KEY is a development placeholder' in text and 'SECRET_KEY is shorter than 32' in text
    assert 'DATABASE_URL contains localhost' in text
    assert 'STRIPE_SECRET_KEY starts with sk_test_' in text
    assert 'hunter2' not in text
    assert live_env.problems(KEYS, {}) == [f"{k['name']} is not set" for k in KEYS]


def test_enforce_stops_the_process_with_the_names(tmp_path, capsys):
    path = tmp_path / 'required-env.json'
    path.write_text(json.dumps({'keys': KEYS + [{'name': 'EXPO_PUBLIC_X', 'service': 'web'}]}))
    with pytest.raises(SystemExit) as stopped:
        live_env.enforce({'SECRET_KEY': 'y' * 40}, path=path)
    assert stopped.value.code == 78
    err = capsys.readouterr().err
    assert 'DATABASE_URL is not set' in err and 'STRIPE_SECRET_KEY is not set' in err
    assert 'EXPO_PUBLIC_X' not in err  # a web build key is not the API's to check
    live_env.enforce({**GOOD}, path=path)  # complete: returns
    live_env.enforce({live_env.SKIP: '1'}, path=path)  # the image build: skipped


def test_without_the_file_the_minimum_is_checked(tmp_path):
    keys = live_env.load_keys(tmp_path / 'absent.json')
    assert {k['name'] for k in keys} == {'SECRET_KEY', 'ALLOWED_HOSTS'}
