# VK E2E



Monorepo scaffolded by VibeKaizen (`django-expo@1.0`).

Database: PostgreSQL everywhere (the platform's in development, previews and staging).

| Part | Path | Run |
|---|---|---|
| API (Django) | `apps/api` | `pip install -r requirements/development.txt && python manage.py migrate && python manage.py runserver` |
| Web (Expo) | `apps/web` | `npm install && npm start` |
| Everything | `infra/docker-compose.yml` | `docker compose -f infra/docker-compose.yml up` |
| The live images, locally | `docker-compose.prod.yml` | `docker compose -f docker-compose.prod.yml up --build`, then http://localhost:8080/healthz |

See `AGENTS.md` for conventions.
