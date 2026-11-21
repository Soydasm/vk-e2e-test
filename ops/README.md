# One-off operational scripts

Data changes belong in a **data migration with reverse code** (`RunPython(forwards, reverse_code=backwards)`,
`RunSQL(sql, reverse_sql=...)`). Only what truly cannot be a migration lives here — a change run once by hand on
the live database (DML, DDL or DCL):

    ops/<name>.py            runs with Django set up: python manage.py shell < ops/<name>.py
    ops/<name>.sql           runs on the app's own database
    ops/<name>.rollback.py   (or .sql) undoes it — required, in the same pull request

A script without its `.rollback` file stops the task before acceptance (the platform checks the pull request). When
the founder rolls the database back with a release, the rollback scripts of the releases being undone run first,
newest first, then the reverse migrations (`python manage.py live_rollback`, docs/live.md). Say in
`.vibekaizen/release_risk.json` `rollback_notes` what each rollback does to the data.
