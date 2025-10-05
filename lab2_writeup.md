# Lab 2 — Deployment & Refactor Writeup

This document summarizes the work done to refactor the note-taking app for a cloud deployment, migrate its data to an external DB, add new features (translation, event fields, generate notes), and the challenges and lessons learned while implementing and testing the changes.

## 🚀 Live Demo
Repo: https://github.com/COMP5241-2526Sem1/note-taking-app-updated-24073779g/blob/main/lab2_writeup.md
The application is deployed and accessible at: **https://24073779g-comp5241-lab2-45tg1q21y-24073779gs-projects.vercel.app**

## Summary of changes
- Migrated data model to use an external Postgres-compatible DB (Supabase). The schema changes are in `supabase/schema.sql`.
- Added event metadata to notes: `event_date` (date) and `event_time` (time).
- Added a translation feature with two backends:
  - LibreTranslate-compatible endpoint (default, configurable via `TRANSLATE_URL`).
  - GitHub Models inference endpoint (model `openai/gpt-4o-mini`) when `USE_GITHUB_MODELS=true` or a token is present.
- Implemented a "Generate Notes" feature (creates placeholder notes programmatically).
- Frontend: updated `src/static/index.html` to show and edit event date/time, add Translate UI, and a Generate Notes button.
- Backend routes and models updated in `src/routes` and `src/models` to support new features.

- Fixed import and dependency issues that prevented the app from starting on Vercel (see "Deployment troubleshooting" below).
- Integrated a Quill rich-text editor in the frontend so note content is stored/edited as HTML. See frontend notes below for XSS and image-upload considerations.

Key edited/added files
- `supabase/schema.sql` — DB schema + ALTER statements to add `event_date` and `event_time`.
- `src/models/note.py` — Note model now includes `event_date` and `event_time`.
- `src/routes/note.py` — Notes endpoints: create, update, list, single note, and new `POST /api/notes/generate` endpoint. Also improved tag handling.
- `src/routes/translate.py` — New translation endpoints and multi-backend support (LibreTranslate + GitHub Models).
- `src/static/index.html` — UI changes: date/time inputs, Translate panel, Generate Notes button, JS handlers.
- `src/lib/supabase_client.py` — now initializes Supabase safely: it no longer raises at import time when environment variables are missing (provides a runtime error when used). This prevents Vercel function import-time crashes.
- `requirements.txt` — added `Flask-SQLAlchemy` so the runtime has the required package on Vercel.

## How to run locally (quick)
1. Install dependencies (make sure the active environment is correct):

```powershell
pip install -r requirements.txt
```

Note: `Flask-SQLAlchemy` was added to `requirements.txt` to ensure SQLAlchemy integration is available on remote deployments (Vercel installs from this file).

2. Configure environment variables (create a `.env` file in the project root or export in your shell):

- `SUPABASE_URL` — your Supabase project URL
- `SUPABASE_ANON_KEY` — Supabase anon/public key
- (Optional) `GITHUB_TOKEN` or `OPENAI_API_KEY` — if you want to use GitHub Models / OpenAI-compatible endpoint
- (Optional) `TRANSLATE_URL` — base URL for a LibreTranslate-compatible instance (default: https://libretranslate.de)
- (Optional) `TRANSLATE_API_KEY` — API key for LibreTranslate if your instance requires one
- (Optional) `USE_GITHUB_MODELS=true` to force using the GitHub Models inference endpoint

Important: if you use a `.env` file locally, do not assume Vercel will read it — Vercel requires environment variables to be configured in the Project Settings (see deployment notes below).

3. Apply the DB schema changes to your Supabase project. The `supabase/schema.sql` file contains the CREATE/ALTER statements. You can run those SQL statements in the Supabase SQL editor or via psql connected to the DB.

4. Start the Flask server:

```powershell
python src\main.py
```

5. Open the UI in your browser:

- http://127.0.0.1:5001/

Try these endpoints (examples):
```powershell
# Create a note with event date/time
curl.exe -X POST http://127.0.0.1:5001/api/notes -H "Content-Type: application/json" -d "{\"title\":\"Meet\", \"content\":\"Plan\", \"event_date\":\"2025-10-10\", \"event_time\":\"14:30:00\"}"

# Generate 3 notes
curl.exe -X POST http://127.0.0.1:5001/api/notes/generate -H "Content-Type: application/json" -d "{\"count\":3, \"prefix\":\"Auto\"}"

# Translate a note (replace <note_id>):
curl.exe -X POST http://127.0.0.1:5001/api/notes/<note_id>/translate -H "Content-Type: application/json" -d "{\"target\":\"en\"}"
```

## Implementation notes and important details
- Tag handling: Supabase nested selects and RLS (Row-Level Security) can cause nested select results to be restricted or structured differently. I added a helper `get_note_tags` which queries the `note_tags` and `tags` tables directly and builds a tag map, then merge tags into notes as a fallback. This makes the API resilient to nested-select differences.

- Translation backends:
  - LibreTranslate-compatible services are used by default via `TRANSLATE_URL` (the code expects a `/translate` endpoint that returns JSON `{ translatedText: '...' }`).
  - For advanced translations using LLMs, the app can call a GitHub Models inference endpoint using model `openai/gpt-4o-mini`. To enable that mode either set `USE_GITHUB_MODELS=true` or make sure `GITHUB_TOKEN`/`OPENAI_API_KEY` is present.
  - The code follows redirects (important for some public LibreTranslate instances that 301 to another domain).

- Frontend changes:
  - `index.html` now includes event date/time inputs and a Translate UI panel, and a simple prompt-based "Generate Notes" flow.
  - When saving a note, the UI now sends `event_date` and `event_time` as part of the payload. When selecting a note the editor populates those inputs from the note returned by the API.

## Challenges encountered
1. Nested selects returning different shapes: Supabase's nested response can be aliased as `tags` or `note_tags` with nested `tag` objects. RLS can also restrict nested content. Solution: query `note_tags` + `tags` separately and build a mapping to ensure correct tag data for each note.

2. 301 redirects from public translation services: some LibreTranslate endpoints redirect (301) to canonical domains. The http client needed follow_redirects=True and proper headers to make the POST succeed.

3. Multiple response shapes from LLM provider: GitHub Models and other providers return different JSON shapes for chat/completions. I added robust parsing to try common patterns (`choices[0].message.content`, `choices[0].text`, etc.).

4. Frontend JS syntax errors during iterative edits — I fixed unbalanced braces and ensured the class methods are correctly closed.

5. Server auto-reloader made debugging logs noisy (server restarted while testing). I turned off the reloader locally during debugging so logs stayed stable.

6. Deployment missing dependencies and env-vars on Vercel: during deployment the function crashed with import-time errors. See the "Deployment troubleshooting" section below for details and the fixes applied.

## Lessons learnt
- Always add small, descriptive debug logs at integration boundaries (DB query, API responses, and critical parsing points). They quickly highlight which layer lost data.
- Use defensive parsing and graceful fallbacks when integrating with external services that can return multiple shapes.
- Prefer feature toggles (env vars) for optional backends rather than hard-coding them. This helps when switching between a free public service and a paid/prod instance.
- For front-end quick features, prompt-based interactions are fast to implement; for production UX, replace them with modals or fully designed forms.

Also: always confirm `requirements.txt` includes all runtime dependencies that your code imports at top-level — serverless platforms install from that file only.

## What I would improve next
- Add formal migrations (e.g., use a migration tool) rather than ad-hoc ALTER SQL in `schema.sql`.
- Implement unit/integration tests for endpoints (notes, tags, translate) to prevent regressions.
- Replace prompt() based generate flow with a modal UI and add options to control event_date/time per generated note.
- Add an option to save translated text back to notes (e.g., create a parallel `translated_content` field or language-tagged versions of notes).
- Add server-side validation for `event_date`/`event_time` formats and better error code handling.

- Add server-side HTML sanitization and an image-upload handler for Quill (uploads can go to Supabase Storage and return a safe URL to embed).

## Files changed (quick map)
- DB: `supabase/schema.sql`
- Models: `src/models/note.py`, `src/models/tag.py`
- Routes: `src/routes/note.py`, `src/routes/tag.py`, `src/routes/translate.py` (added)
- Frontend: `src/static/index.html`
- App entry: `src/main.py` (registered new blueprint)

## Final checklist / verification
- [ ] DB: Run SQL in `supabase/schema.sql` (or use Supabase SQL editor) to ensure `event_date` and `event_time` exist.
- [ ] Env vars: Set SUPABASE_URL and SUPABASE_ANON_KEY.
- [ ] Start server and test: create note with date/time; list and edit note; translation; generate notes.

Deployment troubleshooting (what happened & how it was fixed)

- Symptom: Vercel deployments returned "500: INTERNAL_SERVER_ERROR / FUNCTION_INVOCATION_FAILED". Logs showed an exception during import of `src/models/user.py`:

  ModuleNotFoundError: No module named 'flask_sqlalchemy'

  This prevented the serverless function from initializing because top-level imports raised during the function cold start.

- Fixes applied in this repo:
  - Added `Flask-SQLAlchemy` to `requirements.txt` so Vercel installs the package during build.
  - Reworked `src/lib/supabase_client.py` to avoid raising at import time when `SUPABASE_URL`/`SUPABASE_ANON_KEY` are missing. Instead it provides a small runtime fallback that raises a clear RuntimeError only when Supabase is actually used. This prevents import-time crashes on Vercel when env vars are not yet configured.

- What you must do in Vercel after these changes:
  1. In Vercel dashboard → Project Settings → Environment Variables, add these keys (Production scope):
     - SUPABASE_URL (value copied from your `.env`)
     - SUPABASE_ANON_KEY (value copied from your `.env`)
     - SECRET_KEY (optional, used by Flask sessions)
  2. Redeploy the project (trigger a new deployment or push a commit). Check the deployment logs for any remaining errors.

- Notes about `.env` formatting: avoid spaces around `=` in key=value lines (for example `GITHUB_TOKEN = ...` may create a key with trailing space). Vercel environment variables are set in the dashboard and should not include extra spaces in the key name.

If after redeploying you still see a crash, copy the latest error logs and paste them here — I'll debug the next cause quickly.

## Closing notes
If you want, I can now:
- Add a small modal UI for generating notes and allow adding event_date/time from the modal.
- Implement saving translations back to notes and optionally detect language automatically.
- Create migration scripts and add a tiny test suite for the main endpoints.

If you want screenshots or a PR-ready commit history/log, tell me which parts you'd like documented or committed, and I will prepare them and/or create the PR.
