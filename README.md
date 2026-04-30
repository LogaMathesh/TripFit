# My Dress App

Production-ready dress recommendation app.

## Stack

- Frontend: React + Vite, deployed on Vercel
- Backend: Flask + Gunicorn, deployed on Render
- Database: Supabase PostgreSQL
- Image storage: Cloudinary
- AI: Gemini for image analysis and outfit/search assistance

## Runtime Flow

1. User uploads an image in the React app.
2. Browser uploads the image to Cloudinary using an unsigned, restricted upload preset.
3. React sends the Cloudinary `secure_url` to Flask.
4. Flask analyzes the image with Gemini.
5. Flask stores the Cloudinary URL and recommendation metadata in Supabase PostgreSQL.
6. React displays the result from the backend response and history endpoints.

## Project Structure

```text
.
├── api/                  # Flask backend
│   ├── index.py          # Flask app factory and entrypoint
│   ├── config.py         # Production config from env vars
│   ├── database.py       # Supabase PostgreSQL connection
│   ├── requirements.txt  # Backend dependencies
│   ├── Procfile          # Render startup command
│   ├── routes/           # API routes
│   ├── services/         # Cloudinary and Gemini integrations
│   └── prompts/          # Gemini prompts
├── frontend/             # React/Vite frontend
│   ├── src/
│   ├── package.json
│   └── .env.example
├── supabase_schema.sql   # Supabase schema
├── vercel.json           # Vercel frontend build config
├── .env.example          # Backend + frontend env reference
└── DEPLOYMENT.md         # Step-by-step deployment guide
```

## Local Development

Backend:

```bash
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python index.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Use `.env.example` and `frontend/.env.example` as templates. Do not commit real `.env` files.

## Deployment

See `DEPLOYMENT.md` for Supabase, Cloudinary, Render, and Vercel setup steps.
