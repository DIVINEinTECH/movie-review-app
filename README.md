movie-review-app

A full-stack movie and series review app with user authentication, star ratings, search and filtering. Built with Python Flask and SQLite.

## Features

- User accounts — register, log in, log out with hashed passwords
- Submit reviews — title, type (film/series), star rating (1–5), and written review
- Browse & search — live search by title or review content
- Filter & sort — filter by film vs series, sort by latest or top rated
- Own your reviews — delete your own reviews

## Tech Stack

- Backend — Python 3, Flask, SQLite, Werkzeug for password hashing
- Frontend — Jinja2 templates, vanilla CSS, vanilla JS

## Getting Started

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

Then open http://localhost:5000
