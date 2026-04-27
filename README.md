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

---

## 🛠️ Tech Stack

- **Frontend:** React
- **Backend:** Flask
- **AI Model:** CLIP (openai/clip-vit-large-patch14)
- **Chatbot:** LLM-based
- **Database:** PostgreSQL

---

## 🏃‍♂️ How to Run the Project

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
   pip install -r ../requirements.txt
   ```
4. **Set up the Database and Redis:**
   - Ensure PostgreSQL is running and update the `.env` file with your database credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
   - **Initialize the PostgreSQL tables:**
     You can easily create the required tables by running the provided initialization script from the `backend` directory:
     ```bash
     python init_db.py
     ```
     *Alternatively, you can manually run the following SQL commands in your PostgreSQL database:*
     <details>
     <summary>Click to view SQL Schema</summary>
     
     ```sql
     CREATE TABLE IF NOT EXISTS users (
         id SERIAL PRIMARY KEY,
         username VARCHAR(255) UNIQUE NOT NULL,
         password TEXT NOT NULL
     );

     CREATE TABLE IF NOT EXISTS uploads (
         id SERIAL PRIMARY KEY,
         username VARCHAR(255) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
         image_path TEXT NOT NULL,
         position VARCHAR(255),
         style VARCHAR(255),
         color VARCHAR(255),
         md5_hash VARCHAR(255),
         uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         favorite BOOLEAN DEFAULT FALSE
     );
     ```
     </details>
   - Ensure Redis is running locally on port 6379 (or update `.env` as required).
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

Now, the application should be running! The frontend will typically be on `http://localhost:5173` and the backend API on `http://localhost:5000`.
