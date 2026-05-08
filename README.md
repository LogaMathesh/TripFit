# FitFinder

Comprehensive, end-to-end workflow and system design guide for the FitFinder wardrobe recommendation project.

## Overview

FitFinder is a full-stack application split between:

- `frontend/` — React + Vite single-page app
- `api/` — Flask backend with blueprints and PostgreSQL database access
- External services:
  - Cloudinary for image storage
  - Supabase/PostgreSQL for structured metadata and user data
  - Gemini for image understanding and natural language query generation
  - SerpAPI for online shopping results

This README focuses on the request lifecycle, the data model, and the reasons behind current storage and design decisions.

---

## Architecture Summary

1. User lands on the React SPA.
2. The frontend initializes state from `localStorage` to detect logged-in users and restore the last visited page.
3. User actions on the frontend trigger HTTP requests to the Flask backend.
4. The backend performs business logic, calls external services, and stores metadata in Postgres.
5. The frontend consumes backend responses to render history, suggestions, chatbot results, and profile views.

---

## What happens when the app loads

When the browser opens the app:

- `frontend/src/App.jsx` runs.
- It reads `localStorage.user` and `localStorage.lastView`.
- If a username exists, the app treats the session as authenticated and allows access to:
  - Upload dashboard (`dashboard`)
  - History (`history`)
  - Profile (`profile`)
  - Chatbot (`chatbot`)
  - Idea search (`idea_search`)
- Unauthenticated users can only access:
  - Home
  - Login
  - Signup
  - About

This is a client-side session mechanism only; there is no server-side JWT/session token in the current implementation.

---

## Core stack and responsibilities

### Frontend

- `frontend/src/App.jsx` — routing by view state, `user` state management, and localStorage persistence.
- `frontend/src/lib/api.js` — builds backend URLs using `VITE_API_URL`.
- `frontend/src/pages/Upload.jsx` — accepts image files, uploads them directly to Cloudinary, then sends the Cloudinary URL to the backend.
- `frontend/src/pages/History.jsx` — reads saved uploads from `GET /history/<username>` and allows favorite/delete actions.
- `frontend/src/pages/IdeaSearch.jsx` — sends user text prompts to `/search-ideas` and displays search results.
- `frontend/src/components/Chatbot.jsx` — sends natural language queries to `/chatbot/query` and returns matching wardrobe items.
- `frontend/src/pages/Suggestions.jsx` — uses user wardrobe metadata to suggest saved outfits by `POST /get-suggestions`.
- `frontend/src/pages/Login.jsx` / `Signup.jsx` — calls `/login` and `/signup` respectively.

### Backend

- `api/index.py` — Flask app factory, CORS setup, blueprint registration.
- `api/config.py` — reads environment variables and exposes configuration.
- `api/database.py` — normalizes Supabase DB connection URLs and returns `psycopg` connections.
- `api/init_db.py` — creates tables used by the application.
- `api/routes/*.py` — defines route logic for authentication, uploads, profile, search, chatbot, interactions, and maintenance.
- `api/services/gemini_service.py` — wraps Gemini Vision and text generation calls.
- `api/prompts/gemini_prompts.py` — contains prompt templates for Gemini.

---

## Detailed request workflows

### 1. Signup / Login flow

#### Frontend

- `frontend/src/pages/Signup.jsx` sends `POST /signup` with `{ username, password }`.
- `frontend/src/pages/Login.jsx` sends `POST /login` with `{ username, password }`.

#### Backend

- `api/routes/auth.py` receives the JSON payload.
- For signup, it hashes the password using `werkzeug.security.generate_password_hash(...)` and inserts it into the `users` table.
- For login, it checks the stored hash using `check_password_hash(...)`.

#### Storage

- `users` table stores `username` and `password_hash`.
- Note: the current `api/init_db.py` schema creates `password TEXT NOT NULL`, but the backend writes `password_hash`. This is a schema mismatch that should be fixed.

#### Why this design

- Storing hashed passwords is required for security.
- The current flow is simple, but it is not production-grade because it lacks tokens, sessions, or CSRF protections.

---

### 2. Image upload and classification flow

This is the most important user flow for FitFinder.

#### Frontend steps (`Upload.jsx`)

1. User selects one or more image files.
2. The browser uploads each file directly to Cloudinary using the unsigned upload preset configured in `VITE_CLOUDINARY_UPLOAD_PRESET`.
3. Cloudinary returns a `secure_url` for each uploaded image.
4. The client calls `POST /classify` with `{ image_url, username }`.

#### Backend steps (`uploads.py`)

1. Receive `image_url` and `username`.
2. Compute `md5_hash` of the image URL.
   - This is a simple duplicate check by URL, not by actual image bytes.
3. Query Postgres for an existing upload with the same username and `md5_hash`.
4. If a duplicate exists, return the existing metadata and avoid repeated AI calls.
5. Otherwise, call `services.gemini_service.analyze_dress_image_url(image_url)`.
6. Gemini downloads the image and returns structured metadata.
7. Extract fields:
   - `category -> position`
   - `style`
   - `primary_color -> color`
8. Store the image record in `uploads` with `gemini_metadata` JSON.
9. Return the classification result to the frontend.

#### Storage

`uploads` table columns:

- `id`
- `username`
- `image_path` — Cloudinary URL
- `position`, `style`, `color`
- `md5_hash` — de-duplication key
- `uploaded_at`
- `favorite`
- `gemini_metadata` — raw JSON from Gemini

#### Why this design

- Cloudinary stores large binary assets so the database remains lightweight.
- Postgres stores structured metadata for search, grouping, and filtering.
- Keeping raw `gemini_metadata` enables later improvements without re-analyzing images.
- The duplicate check prevents unnecessary AI usage and cost.

---

### 3. History and favorites flow

#### Frontend

- `History.jsx` calls `GET /history/<username>`.
- Displays upload cards grouped by style and sorted by date.
- Allows users to:
  - Toggle favorite status via `POST /toggle_favorite`
  - Delete uploads via `POST /delete_upload`

#### Backend

- `/history/<username>` returns the full latest upload set for that user.
- `/toggle_favorite` flips the boolean `favorite` value for the specified upload.
- `/delete_upload` removes the row from `uploads`.

#### Why this design

- The user-facing history page depends on structured attributes, not raw image blobs.
- Favorites are stored in the same table to keep queries simple.
- This is currently a denormalized design that trades some flexibility for fewer joins.

---

### 4. Suggestions flow

#### Frontend

- `Suggestions.jsx` sends `POST /get-suggestions` with `{ destination, username }`.
- Uses the selected destination to filter previously uploaded outfit metadata.

#### Backend

- Queries `uploads` filtering by `style = destination` and `username`.
- Returns the most recent unique uploads by `md5_hash`.

#### Why this design

- This is a lightweight personalization feature built from existing wardrobe items.
- It avoids new AI calls by reusing previously analyzed uploads.

---

### 5. Idea search flow

This is the “shopping idea” flow.

#### Frontend

- `IdeaSearch.jsx` sends user text to `POST /search-ideas`.
- Displays results from Google Shopping (via SerpAPI).
- Allows in-page interaction events like `like`, `dislike`, and `save` using `POST /interact`.

#### Backend

1. Fetch user profile data from `user_profiles` if `username` exists.
2. Fetch recent `user_interactions` for feedback.
3. Build a Gemini prompt that converts a natural description into a concrete shopping query.
4. Call Gemini text generation.
5. Save the generated query to `search_logs`.
6. Call SerpAPI for Google Shopping results.
7. Return cleaned search result cards to the frontend.

#### Storage

- `user_profiles` — persisted user preferences (gender, budget, sizes, style).
- `search_logs` — raw prompt and transformed query.
- `user_interactions` — user feedback on search results.

#### Why this design

- Profile and interaction logs provide personalization context for query generation.
- Logging search prompts enables future analytics or retraining.
- Separating the model query from raw result storage keeps costs lower and preserves privacy of actual shopping results.

---

### 6. Chatbot flow

#### Frontend

- `Chatbot.jsx` sends `{ user_id, query }` to `POST /chatbot/query`.
- The returned results are wardrobe items ranked by relevance.

#### Backend

1. Query the user’s saved uploads and raw `gemini_metadata`.
2. Build a list of wardrobe items with style, color, position, and metadata.
3. Pass them to `services.gemini_service.suggest_matching_items(query, wardrobe_items)`.
4. Gemini returns a ranked list of URLs.
5. The backend formats results and sends them back.

#### Why this design

- This flow uses the user’s own wardrobe as the knowledge base.
- The backend does not re-run image analysis; it reuses previously stored metadata.
- It is a lightweight retrieval-style recommendation on top of a small dataset.

---

### 7. Maintenance and background indexing

Routes in `api/routes/maintenance.py` provide cleanup and metadata indexing utilities:

- `/check-duplicates` — detects duplicate `image_path` rows.
- `/clean-duplicates` — removes duplicate upload records.
- `/index-existing-images` — analyzes any existing uploads missing `gemini_metadata`.

#### Why this exists

- It supports backfilling older records if analysis was skipped or the schema changed.
- It is a simple way to keep the dataset consistent without re-uploading images.

---

## Database model details

### `users`

- `id`
- `username` — unique login key.
- `password` / `password_hash` — should be hashed.

### `uploads`

- `username` — foreign key to users.
- `image_path` — Cloudinary URL.
- `position`, `style`, `color` — normalized metadata for filters.
- `md5_hash` — dedupe key based on image URL.
- `uploaded_at`
- `favorite`
- `gemini_metadata` — raw JSON from Gemini.

### `user_profiles`

- Stores user preferences used for idea search personalization.
- `sizes`, `budget_level`, `style_preferences`, etc.

### `search_logs`

- Used to audit what prompts users entered and what concrete query Gemini generated.
- Great for future optimization or analytics.

### `user_interactions`

- Stores `like`, `dislike`, and `save` events from idea search results.
- Useful for adaptive personalization.

---

## Design issues and important notes

### Current authentication is not production-ready

- The frontend stores only `username` in `localStorage`.
- The backend does not issue JWTs or secure sessions.
- This should be upgraded to a secure auth token mechanism before scaling.

### Duplicate detection is URL-based, not image-based

- The backend uses `md5(image_url)`.
- If the same image is uploaded via a different URL, it may not be detected as duplicate.
- A better design would hash the file bytes or use a perceptual hash.

### Raw Gemini metadata is preserved intentionally

- `gemini_metadata` lets you build better search, recommendation, and analytics later.
- It also makes it possible to re-map fields if the prompt evolves.

### The backend currently mixes responsibilities

- Image ingestion,
- AI analysis,
- personalization,
- search logging,
- and cleanup utilities

That is fine for a small app, but for scaling you should split into services.

---

## Scaling recommendations

### Short-term improvements

- Add request-level authentication with tokens.
- Add input validation and sanitization for all endpoints.
- Add pagination to `/history/<username>` and `/search-ideas`.
- Add indexes on `uploads(username)`, `uploads(md5_hash)`, `search_logs(username)`, `user_interactions(username)`.
- Use connection pooling instead of raw `psycopg.connect(...)` for each request.
- Move expensive AI calls to asynchronous background workers.

### Medium-term architecture

- Separate services:
  - Auth service
  - Upload ingestion service
  - AI analysis worker
  - Recommendation/search service
  - User profile and analytics service
- Use a message queue for heavy tasks:
  - Cloudinary upload completed -> backend task -> Gemini analysis -> store metadata
- Store audit logs in a separate analytics schema or data warehouse.

### Long-term scaling

- Replace the direct frontend Cloudinary upload preset with signed uploads.
- Move from Flask monolith to microservices or serverless endpoints when traffic grows.
- Add read replicas for the Postgres database if history/query traffic becomes large.
- Cache common results and the output of `/get-suggestions`, `/history`, and `/chatbot/query`.
- Use a dedicated vector store for semantic wardrobe search if you need better AI matching at scale.

---

## Local development

### Backend

```powershell
cd api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python index.py
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Environment configuration

- Backend config is read from `api/config.py` and `.env` files.
- Frontend config is read from `frontend/.env` and `import.meta.env`.
- The key variables are:
  - `SUPABASE_DB_URL`
  - `GEMINI_API_KEY`
  - `SERPAPI_KEY`
  - `CLOUDINARY_CLOUD_NAME`
  - `VITE_CLOUDINARY_UPLOAD_PRESET`
  - `VITE_API_URL`

---

## Directory structure

```text
.
├── api/
│   ├── config.py
│   ├── database.py
│   ├── index.py
│   ├── init_db.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py
│   │   ├── uploads.py
│   │   ├── profile.py
│   │   ├── idea_search.py
│   │   ├── chatbot.py
│   │   ├── interactions.py
│   │   └── maintenance.py
│   ├── services/
│   │   └── gemini_service.py
│   └── prompts/
│       └── gemini_prompts.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── lib/api.js
│   │   └── pages/
│   └── .env.example
├── supabase_schema.sql
├── vercel.json
├── DEPLOYMENT.md
└── README.md
```

---

## Key takeaways for system design

- This project is a data-driven wardrobe assistant where the user object is the center of every request.
- Images are kept out of the database; metadata is stored in Postgres and raw assets in Cloudinary.
- Gemini is used both for vision analysis and for transforming text into search queries.
- The current auth/session design is minimal and must be upgraded before production scaling.
- Future scaling should focus on:
  - stronger authentication,
  - background AI processing,
  - efficient database access,
  - and separation of responsibilities.
