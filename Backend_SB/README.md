# Smart Bee Backend

AI-powered backend for Smart Bee email assistant.

## Components
- brain.py → AI decision engine
- api.py → REST API layer
- gmail_service.py → email abstraction
- scheduler.py → reminders & scheduling
- SQLite → logging (optional)

## Run
```bash
uvicorn api:app --reload
