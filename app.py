from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cinereview-dev-secret-key')
DATABASE = 'cinereview.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('movie', 'series')),
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                review_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        db.commit()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to do that.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    db = get_db()
    query = request.args.get('q', '').strip()
    filter_type = request.args.get('type', 'all')
    sort = request.args.get('sort', 'latest')

    sql = '''
        SELECT r.*, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    '''
    params = []

    if query:
        sql += ' AND (r.title LIKE ? OR r.review_text LIKE ?)'
        params += [f'%{query}%', f'%{query}%']

    if filter_type in ('movie', 'series'):
        sql += ' AND r.type = ?'
        params.append(filter_type)

    if sort == 'top':
        sql += ' ORDER BY r.rating DESC, r.created_at DESC'
    else:
        sql += ' ORDER BY r.created_at DESC'

    reviews = db.execute(sql, params).fetchall()

    stats = db.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN type = "movie" THEN 1 ELSE 0 END) as movies,
            SUM(CASE WHEN type = "series" THEN 1 ELSE 0 END) as series,
            ROUND(AVG(rating), 1) as avg_rating
        FROM reviews
    ''').fetchone()

    return render_template('index.html', reviews=reviews, query=query,
                           filter_type=filter_type, sort=sort, stats=stats)


@app.route('/review/<int:review_id>')
def review_detail(review_id):
    db = get_db()
    review = db.execute('''
        SELECT r.*, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    ''', (review_id,)).fetchone()
    if not review:
        flash('Review not found.', 'error')
        return redirect(url_for('index'))
    return render_template('review_detail.html', review=review)


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content_type = request.form.get('type', '')
        rating = request.form.get('rating', '')
        review_text = request.form.get('review_text', '').strip()
        errors = []

        if not title:
            errors.append('Title is required.')
        if content_type not in ('movie', 'series'):
            errors.append('Please select Movie or Series.')
        if not rating.isdigit() or int(rating) not in range(1, 6):
            errors.append('Rating must be between 1 and 5.')
        if len(review_text) < 20:
            errors.append('Review must be at least 20 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('submit.html', form=request.form)

        db = get_db()
        db.execute('''
            INSERT INTO reviews (user_id, title, type, rating, review_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], title, content_type, int(rating), review_text,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('index'))

    return render_template('submit.html', form={})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        errors = []

        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if '@' not in email:
            errors.append('Enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if not errors:
            db = get_db()
            try:
                db.execute('''
                    INSERT INTO users (username, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, generate_password_hash(password),
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                db.commit()
                user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'Welcome, {username}!', 'success')
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                flash('Username or email already taken.', 'error')
        else:
            for e in errors:
                flash(e, 'error')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    db = get_db()
    review = db.execute('SELECT * FROM reviews WHERE id = ?', (review_id,)).fetchone()
    if not review:
        flash('Review not found.', 'error')
    elif review['user_id'] != session['user_id']:
        flash('You can only delete your own reviews.', 'error')
    else:
        db.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
        db.commit()
        flash('Review deleted.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)