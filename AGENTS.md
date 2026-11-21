# VK E2E — agent guide

Bu proje VibeKaizen platformunda geliştirilmektedir.

Database: PostgreSQL everywhere (the platform's in development, previews and staging).

## Layout
- `apps/api` — Django 5 + DRF. Auth (`apps/users`), `GET /healthz/`, `GET /api/v1/hello/`.
- `apps/web` — Expo web (React Native Web) with expo-router. Routes in `apps/web/app/` (`app/index.tsx` is `/`),
  shared layers in `apps/web/src/`: `theme/` (light + dark tokens, motion tokens), `components/` (the UI kit and
  `motion.tsx`; `/ui-kit` shows it), `i18n/` (English strings per feature in `messages/<feature>.ts`, other languages in `locales/<language>/`), `api/client.ts` (the only place that calls the API; unwraps the response envelope). Playwright e2e in `apps/web/e2e`.
- `.vibekaizen/project.yaml` — commands the platform runs (install / migrate / start / test / e2e). Keep it valid YAML.

## Where to look before you build
- `PRODUCT_STATE.md` — what the product currently *is*: every route and what it builds on, the shared
  components and which screens use them, the API surface, and the decisions earlier tasks settled. The
  platform regenerates it after each task; never hand-edit it. This file is how you avoid adding a second
  version of a screen that already exists.
- `.vibekaizen/memory/project/` — what earlier tasks wrote down for you (gotchas, where things live).

## Conventions
- Backend: one Django app per domain under `apps/api/apps/<domain>/`; DRF `APIView`/`ViewSet`; every endpoint under `/api/v1/`.
- Every backend endpoint ships with a pytest in `apps/api/tests/<domain>/`. `pytest -q` must pass.
- Frontend: TypeScript strict. A new screen is a route file under `apps/web/app/`. Read colors, spacing and
  typography from `useTheme()`, text from `useI18n().t`, data through `api` — never a hardcoded color, a
  literal sentence, or a `fetch` inside a component. Render all four states: loading, error, empty, content.
- Motion: durations and curves from `theme.motion`, through `src/components/motion.tsx` (`FadeIn`, `PressScale`,
  `ListItemEnter`) — never a literal duration — only to show what changed, never on every render or in a loop
  (a loading indicator aside), and nothing moves when `theme.motion.reducedMotion` is on.
- Strings: a feature keeps its English strings in its own `apps/web/src/i18n/messages/<feature>.ts` and adds the
  file to `messages/index.ts`; for each other language the app speaks (the folders in `apps/web/src/i18n/locales/`)
  it adds `locales/<language>/<feature>.ts` with the same keys and one line to that language's `index.ts`. A new
  language is one new folder and one line in `locales/index.ts` (the recipe is at the top of that file).
  `npx tsc --noEmit` fails on a language that misses a key and on a `t('…')` key that does not exist. Plurals are `x.one` / `x.other` keys read with
  `tn('x', count)`. Prices, numbers and dates go through `useI18n().format` (`money`, `number`, `date`,
  `time`) — never `toFixed`, a hardcoded currency sign or a hand-built date string.
- The backend answers in the request's language (`LocaleMiddleware`); errors carry a stable `error_code` the
  web app translates. Data the user enters is stored as entered.
- `/ui-kit` is the kit's preview for the people building the app, not a product screen: nothing in the app
  links to it, and no task adds a "design system" or "components" screen to the navigation.
- Every user-visible feature ships with a Playwright e2e in `apps/web/e2e/` that asserts the acceptance criteria.
- The whole suite passes in one run. A rate limit, a cooldown or a time-based guard you add reads `DEBUG`
  (on in the development container and the preview, off in production) and is scaled up or off there — a
  60/min sign-in limit broke the full e2e run and cost two gate rounds (habit tracker, 13 October 2026).
  Never loosen a limit by hand for one run, and never run a failing spec alone to call it green.
- Migrations must be backward compatible (no column drops/renames in the same release as the code change).

## Do not touch
- `PRODUCT_STATE.md` — the platform writes it from the code after every task.
- `.vibekaizen/project.yaml` `parts.*.dir` and ports.
- `apps/api/config/settings/*` beyond adding app-specific settings at the bottom.
- `apps/api/apps/core/dto.py` (response envelope) and `apps/api/apps/users` auth flow.
- The shape of `apps/web/src/theme`, `apps/web/src/i18n` and `apps/web/src/api/client.ts`: extend them
  (add tokens, keys, endpoints) rather than replacing them or working around them.
- The live setup, which the platform maintains: `infra/` (the images and the Caddyfile), `docker-compose.prod.yml`,
  `.dockerignore`, `deploy/required-env.json`, `apps/api/config/live_env.py`, `apps/api/apps/core/health.py` and the
  "go-live" block at the end of `config/settings/production.py`, and once the project goes live `render.yaml` and
  `docs/live.md` (a change to any of them waits for the founder's approval). A key the live app needs is declared in
  `.vibekaizen/project.yaml` `env` (`provided_by: user`, `envs` including `production`); the platform adds it to
  `deploy/required-env.json`, and the live app then refuses to start without it.
- Every migration has its reverse (RunPython `reverse_code`, RunSQL `reverse_sql`; a `.noop` reverse only with its
  reason in `.vibekaizen/release_risk.json` `rollback`), and every one-off script in `ops/` ships with its
  `ops/<name>.rollback.py` or `.sql` (see `ops/README.md`).

## Definition of done
- Acceptance criteria satisfied and covered by tests (api pytest + web e2e).
- `pytest -q` (api), `npx tsc --noEmit` (web) pass locally.
- No secrets in code; new env vars are declared in `.vibekaizen/project.yaml` `env`.

## Lessons (updated by the platform after each sprint retro)
- (none yet)

## Lessons — Retro — E2E
- Lessons reach main through a PR
