# Production Deployment

## Recommended Hosting

- Frontend: Vercel free tier.
- Backend: Render free tier for the Flask API. Render is the simpler choice here because it supports a persistent Python web service with a `Procfile` and environment variables without adapting Flask to serverless.
- Database: Supabase PostgreSQL free tier.
- Images: Cloudinary free tier with unsigned browser uploads and automatic quality/format optimization.

## Environment Variables

Paste backend variables into Render under Web Service > Environment:

- `SUPABASE_DB_URL`: Supabase Project Settings > Database > Connection string > Transaction pooler or Session pooler. Include `?sslmode=require`.
- `SUPABASE_URL`: Supabase Project Settings > API > Project URL.
- `SUPABASE_ANON_KEY`: Supabase Project Settings > API > anon public key.
- `CLOUDINARY_CLOUD_NAME`: Cloudinary Dashboard > Cloud name.
- `CLOUDINARY_API_KEY`: Cloudinary Dashboard > API key.
- `CLOUDINARY_API_SECRET`: Cloudinary Dashboard > API secret.
- `GEMINI_API_KEY`: Google AI Studio API key.
- `SERPAPI_KEY`: SerpAPI key, only if `/search-ideas` is enabled.
- `FRONTEND_URL`: Your Vercel URL, for example `https://my-dress-app.vercel.app`.
- `CORS_ORIGINS`: Same Vercel URL plus local dev if needed: `https://my-dress-app.vercel.app,http://localhost:5173`.
- `SECRET_KEY`: Any long random string.

Paste frontend variables into Vercel under Project Settings > Environment Variables:

- `VITE_API_URL`: Your Render backend URL, for example `https://my-dress-api.onrender.com`.
- `VITE_CLOUDINARY_CLOUD_NAME`: Cloudinary Dashboard > Cloud name.
- `VITE_CLOUDINARY_UPLOAD_PRESET`: Cloudinary unsigned upload preset name.

## Supabase Setup

1. Create a Supabase project.
2. Open SQL Editor and run `supabase_schema.sql`.
3. Copy the pooled database connection string into `SUPABASE_DB_URL`.
4. Use the anon key only for public frontend Supabase clients. This app currently uses Flask for database access, so keep database credentials on the backend only.

## Cloudinary Setup

1. Create an unsigned upload preset.
2. Restrict the preset to images, set folder to `my_dress_app`, and enable transformations:
   - format: auto
   - quality: auto or eco
   - max dimensions around 1200 px
3. Put the preset name in `VITE_CLOUDINARY_UPLOAD_PRESET`.

## Render Backend

1. Create a new Render Web Service from the GitHub repo.
2. Root directory: `api`.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn index:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`.
5. Add the backend environment variables listed above.
6. Deploy and confirm `/chatbot/status` returns JSON.

## Vercel Frontend

1. Import the GitHub repo into Vercel.
2. Use the repository root as the project root.
3. Vercel will use `vercel.json` to build `frontend`.
4. Add the frontend environment variables listed above.
5. Deploy.
6. Copy the final Vercel domain back into Render as `FRONTEND_URL` and `CORS_ORIGINS`.

## Deployment Checklist

- No `.env`, `.venv`, `node_modules`, `dist`, local uploads, or model weights committed.
- `FLASK_DEBUG=0` in production.
- `CORS_ORIGINS` contains only trusted frontend domains.
- Supabase schema has `users.password_hash`, not `users.password`.
- Cloudinary upload preset is unsigned but restricted to image uploads.
- Gemini and SerpAPI keys exist only on the backend.
- `VITE_API_URL` points to the live backend.
- Upload flow works: browser uploads to Cloudinary, frontend sends `secure_url` to Flask, Flask analyzes with Gemini, result saves in Supabase, frontend renders result.
