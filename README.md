# 👗 AI-Based Dress Classification & Recommendation System

A simple AI-powered web application that classifies dress images, recommends suitable outfits based on destination, and provides an AI chatbot for fashion-related queries.

---

## 📌 Project Overview

This project allows users to:
- Upload dress images
- Get dress classification using an AI model
- Receive destination-based outfit recommendations
- Interact with an AI chatbot for fashion advice

---

## 🏗️ System Architecture

![System Architecture](./architecture-diagram.png)

**Description:**
- Users interact with the system through a React frontend.
- The frontend communicates with a Flask backend using REST APIs.
- The backend handles image uploads, recommendations, and chatbot requests.
- A CLIP model is used for dress image classification.
- The chatbot uses an LLM and can optionally retrieve context from a vector database.
- PostgreSQL stores structured data and image metadata.

---

## 🚀 Features

- Dress image classification using CLIP
- Destination-based dress recommendations
- AI chatbot for user queries
- Admin panel with CSV export
- PostgreSQL database support
- Celery background tasks (Redis)

---

## 🛠️ Tech Stack

- **Frontend:** React, Vite
- **Backend:** Flask
- **AI Model:** CLIP (openai/clip-vit-large-patch14)
- **Chatbot:** LLM-based (Gemini)
- **Database:** PostgreSQL
- **Background Tasks:** Celery, Redis

---

## 🐳 Docker Setup (Recommended)

The easiest way to run the application is using Docker. This will set up the frontend, backend, PostgreSQL database, Redis, and Celery worker automatically.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Steps

1. **Clone the repository and navigate to the project root:**
   ```bash
   git clone <your-repo-url>
   cd My-Dress-App
   ```

2. **Configure Environment Variables:**
   Copy `.env.example` to `.env` in the root directory:
   ```bash
   cp .env.example .env
   ```
   *Note: Open `.env` and fill in your actual `GEMINI_API_KEY`, `SERPAPI_KEY`, and `GOOGLE_API_KEY`.*

3. **Build and Run the Containers:**
   ```bash
   docker compose up --build
   ```

4. **Initialize the Database:**
   Once the containers are running, initialize the database schema by executing the init script inside the backend container (only needed once):
   ```bash
   docker compose exec backend python init_db.py
   ```

### Ports Used
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:5000
- **PostgreSQL:** 5432
- **Redis:** 6379

### Troubleshooting (Docker)
- If the backend fails to connect to the database, ensure you didn't change the `DB_HOST=db` in the `.env` file for Docker.
- If changes to the frontend/backend don't reflect, you may need to rebuild the images: `docker compose up --build`.

---

## 🏃‍♂️ Manual Setup (Without Docker)

<details>
<summary>Click here to view manual setup instructions</summary>

### Prerequisites
- Node.js (for frontend)
- Python 3.8+ (for backend)
- PostgreSQL
- Redis Server (for Celery background tasks)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up the Database and Redis:**
   - Ensure PostgreSQL is running and update the `.env` file with your database credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST=localhost`, `DB_PORT`).
   - **Initialize the PostgreSQL tables:**
     ```bash
     python init_db.py
     ```
   - Ensure Redis is running locally on port 6379 (or update `REDIS_URL` in `.env`).
   - Set up your API keys in the `.env` file (e.g., Gemini API, SerpAPI).

5. **Run the Flask application:**
   ```bash
   python app.py
   ```

6. **Run the Celery Worker (in a separate terminal):**
   ```bash
   cd backend
   .venv\Scripts\activate
   # Start the celery worker:
   celery -A async_tasks.celery_setup.celery_instance worker --loglevel=info -P gevent
   ```

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend/"dress react"
   ```
2. **Install frontend dependencies:**
   ```bash
   npm install
   ```
3. **Start the development server:**
   ```bash
   npm run dev
   ```

</details>
