-- Run this in the Supabase SQL Editor

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    gender VARCHAR(50),
    budget_level VARCHAR(100),
    sizes TEXT,
    style_preferences TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Uploads
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    image_path TEXT NOT NULL, -- This will store the Cloudinary URL
    position VARCHAR(100),
    style VARCHAR(100),
    color VARCHAR(100),
    md5_hash VARCHAR(32), -- Used to hash the Cloudinary URL to prevent duplicates
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    favorite BOOLEAN DEFAULT FALSE,
    gemini_metadata JSONB
);

-- 4. Search Logs (History)
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
    raw_prompt TEXT NOT NULL,
    generated_query TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. User Interactions
CREATE TABLE IF NOT EXISTS user_interactions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
    title TEXT,
    price VARCHAR(100),
    link TEXT,
    thumbnail TEXT,
    source VARCHAR(255),
    interaction_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
