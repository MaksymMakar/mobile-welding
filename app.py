"""
Ironclad Welding — Flask backend.
Run:  python app.py
Default admin login:  admin / admin123  (change immediately in /admin/settings)
"""
import os
import re
import secrets
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, send_from_directory, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

import db

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_IMAGE_WIDTH = 1600

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB uploads

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- helpers ----------

def slugify(text):
    text = (text or '').lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'item'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def save_upload(file_storage):
    """Save uploaded image, downscale large ones, return public path."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}.{ext}"
    name = secure_filename(name)
    path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(path)
    try:
        img = Image.open(path)
        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / img.width
            img = img.resize((MAX_IMAGE_WIDTH, int(img.height * ratio)), Image.LANCZOS)
            img.save(path, optimize=True, quality=85)
    except Exception:
        pass
    return f'uploads/{name}'


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('admin_login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_globals():
    return {
        'settings': db.get_all_settings(),
        'current_year': datetime.now().year,
        'is_admin': bool(session.get('user_id')),
    }


# ---------- public routes ----------

@app.route('/')
def home():
    conn = db.get_db()
    services = conn.execute(
        'SELECT * FROM services WHERE is_active = 1 ORDER BY sort_order, id LIMIT 6'
    ).fetchall()
    testimonials = conn.execute(
        'SELECT * FROM testimonials WHERE is_active = 1 ORDER BY created_at DESC LIMIT 6'
    ).fetchall()
    faqs = conn.execute(
        'SELECT * FROM faqs WHERE is_active = 1 ORDER BY sort_order, id'
    ).fetchall()
    gallery = conn.execute(
        'SELECT * FROM gallery ORDER BY sort_order, created_at DESC LIMIT 6'
    ).fetchall()
    conn.close()
    return render_template('index.html',
                           services=services,
                           testimonials=testimonials,
                           faqs=faqs,
                           gallery=gallery)


@app.route('/services')
def services_page():
    conn = db.get_db()
    services = conn.execute(
        'SELECT * FROM services WHERE is_active = 1 ORDER BY sort_order, id'
    ).fetchall()
    conn.close()
    return render_template('services.html', services=services)


@app.route('/services/<slug>')
def service_detail(slug):
    conn = db.get_db()
    service = conn.execute(
        'SELECT * FROM services WHERE slug = ? AND is_active = 1', (slug,)
    ).fetchone()
    conn.close()
    if not service:
        abort(404)
    return render_template('service_detail.html', service=service)


@app.route('/gallery')
def gallery_page():
    conn = db.get_db()
    items = conn.execute(
        'SELECT * FROM gallery ORDER BY sort_order, created_at DESC'
    ).fetchall()
    conn.close()
    return render_template('gallery.html', items=items)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        service = (request.form.get('service') or '').strip()
        budget = (request.form.get('budget') or '').strip()
        message = (request.form.get('message') or '').strip()

        if not (name and email and message):
            flash('Please fill in your name, email and a short message.', 'error')
            return redirect(url_for('contact_page'))

        conn = db.get_db()
        conn.execute(
            'INSERT INTO quotes (name, email, phone, service, budget, message) VALUES (?, ?, ?, ?, ?, ?)',
            (name, email, phone, service, budget, message)
        )
        conn.commit()
        conn.close()
        flash('Thanks — your quote request is in. We typically reply within 4 business hours.', 'success')
        return redirect(url_for('contact_page'))

    conn = db.get_db()
    services = conn.execute(
        'SELECT title FROM services WHERE is_active = 1 ORDER BY sort_order'
    ).fetchall()
    conn.close()
    return render_template('contact.html', services=services)


@app.route('/sitemap.xml')
def sitemap():
    conn = db.get_db()
    services = conn.execute('SELECT slug FROM services WHERE is_active = 1').fetchall()
    conn.close()
    pages = ['', 'services', 'gallery', 'about', 'contact']
    urls = [request.url_root + p for p in pages]
    urls += [request.url_root + f'services/{s["slug"]}' for s in services]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        body += f'  <url><loc>{u}</loc></url>\n'
    body += '</urlset>\n'
    return body, 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt')
def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {request.url_root}sitemap.xml\n", 200, {'Content-Type': 'text/plain'}


# ---------- admin auth ----------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        conn = db.get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}.', 'success')
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Signed out.', 'success')
    return redirect(url_for('home'))


# ---------- admin dashboard ----------

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = db.get_db()
    counts = {
        'services': conn.execute('SELECT COUNT(*) FROM services').fetchone()[0],
        'gallery': conn.execute('SELECT COUNT(*) FROM gallery').fetchone()[0],
        'testimonials': conn.execute('SELECT COUNT(*) FROM testimonials').fetchone()[0],
        'quotes_new': conn.execute("SELECT COUNT(*) FROM quotes WHERE status='new'").fetchone()[0],
        'quotes_total': conn.execute('SELECT COUNT(*) FROM quotes').fetchone()[0],
    }
    recent_quotes = conn.execute(
        'SELECT * FROM quotes ORDER BY created_at DESC LIMIT 5'
    ).fetchall()
    conn.close()
    return render_template('admin/dashboard.html', counts=counts, recent_quotes=recent_quotes)


# ---------- admin: services ----------

@app.route('/admin/services')
@login_required
def admin_services():
    conn = db.get_db()
    items = conn.execute('SELECT * FROM services ORDER BY sort_order, id').fetchall()
    conn.close()
    return render_template('admin/services.html', items=items)


@app.route('/admin/services/new', methods=['GET', 'POST'])
@app.route('/admin/services/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_service_form(item_id=None):
    conn = db.get_db()
    item = None
    if item_id:
        item = conn.execute('SELECT * FROM services WHERE id = ?', (item_id,)).fetchone()
        if not item:
            conn.close()
            abort(404)

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        short_desc = (request.form.get('short_desc') or '').strip()
        long_desc = (request.form.get('long_desc') or '').strip()
        icon = (request.form.get('icon') or 'flame').strip()
        price_from = (request.form.get('price_from') or '').strip()
        sort_order = int(request.form.get('sort_order') or 0)
        is_active = 1 if request.form.get('is_active') else 0

        if not (title and short_desc):
            flash('Title and short description are required.', 'error')
            conn.close()
            return redirect(request.url)

        image_path = item['image'] if item else None
        if 'image' in request.files:
            new_image = save_upload(request.files['image'])
            if new_image:
                image_path = new_image

        slug = slugify(title)

        if item:
            conn.execute(
                'UPDATE services SET title=?, slug=?, short_desc=?, long_desc=?, icon=?, price_from=?, image=?, is_active=?, sort_order=? WHERE id=?',
                (title, slug, short_desc, long_desc, icon, price_from, image_path, is_active, sort_order, item_id)
            )
            flash('Service updated.', 'success')
        else:
            # ensure unique slug
            base_slug, n = slug, 2
            while conn.execute('SELECT 1 FROM services WHERE slug=?', (slug,)).fetchone():
                slug = f'{base_slug}-{n}'
                n += 1
            conn.execute(
                'INSERT INTO services (title, slug, short_desc, long_desc, icon, price_from, image, is_active, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, slug, short_desc, long_desc, icon, price_from, image_path, is_active, sort_order)
            )
            flash('Service added.', 'success')
        conn.commit()
        conn.close()
        return redirect(url_for('admin_services'))

    conn.close()
    icons = ['flame', 'zap', 'target', 'bolt', 'hammer', 'truck', 'scissors', 'wrench', 'shield', 'sparkles']
    return render_template('admin/service_form.html', item=item, icons=icons)


@app.route('/admin/services/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_service_delete(item_id):
    conn = db.get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Service deleted.', 'success')
    return redirect(url_for('admin_services'))


# ---------- admin: gallery ----------

@app.route('/admin/gallery', methods=['GET', 'POST'])
@login_required
def admin_gallery():
    conn = db.get_db()
    if request.method == 'POST':
        title = (request.form.get('title') or 'Untitled').strip()
        caption = (request.form.get('caption') or '').strip()
        category = (request.form.get('category') or 'general').strip()
        sort_order = int(request.form.get('sort_order') or 0)
        image_path = save_upload(request.files.get('image'))
        if not image_path:
            flash('Please pick a valid image file.', 'error')
        else:
            conn.execute(
                'INSERT INTO gallery (title, caption, image, category, sort_order) VALUES (?, ?, ?, ?, ?)',
                (title, caption, image_path, category, sort_order)
            )
            conn.commit()
            flash('Image added to gallery.', 'success')
        conn.close()
        return redirect(url_for('admin_gallery'))

    items = conn.execute('SELECT * FROM gallery ORDER BY sort_order, created_at DESC').fetchall()
    conn.close()
    return render_template('admin/gallery.html', items=items)


@app.route('/admin/gallery/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_gallery_delete(item_id):
    conn = db.get_db()
    row = conn.execute('SELECT image FROM gallery WHERE id = ?', (item_id,)).fetchone()
    if row and row['image']:
        try:
            os.remove(os.path.join(BASE_DIR, 'static', row['image']))
        except OSError:
            pass
    conn.execute('DELETE FROM gallery WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Image removed.', 'success')
    return redirect(url_for('admin_gallery'))


# ---------- admin: testimonials ----------

@app.route('/admin/testimonials', methods=['GET', 'POST'])
@login_required
def admin_testimonials():
    conn = db.get_db()
    if request.method == 'POST':
        author = (request.form.get('author') or '').strip()
        role = (request.form.get('role') or '').strip()
        body = (request.form.get('body') or '').strip()
        rating = int(request.form.get('rating') or 5)
        if not (author and body):
            flash('Author and body required.', 'error')
        else:
            conn.execute(
                'INSERT INTO testimonials (author, role, body, rating) VALUES (?, ?, ?, ?)',
                (author, role, body, rating)
            )
            conn.commit()
            flash('Testimonial added.', 'success')
        conn.close()
        return redirect(url_for('admin_testimonials'))

    items = conn.execute('SELECT * FROM testimonials ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/testimonials.html', items=items)


@app.route('/admin/testimonials/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_testimonial_delete(item_id):
    conn = db.get_db()
    conn.execute('DELETE FROM testimonials WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('admin_testimonials'))


# ---------- admin: quotes ----------

@app.route('/admin/quotes')
@login_required
def admin_quotes():
    conn = db.get_db()
    items = conn.execute('SELECT * FROM quotes ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/quotes.html', items=items)


@app.route('/admin/quotes/<int:item_id>/status', methods=['POST'])
@login_required
def admin_quote_status(item_id):
    status = (request.form.get('status') or 'new').strip()
    if status not in ('new', 'contacted', 'won', 'lost'):
        status = 'new'
    conn = db.get_db()
    conn.execute('UPDATE quotes SET status=? WHERE id=?', (status, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_quotes'))


@app.route('/admin/quotes/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_quote_delete(item_id):
    conn = db.get_db()
    conn.execute('DELETE FROM quotes WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Quote deleted.', 'success')
    return redirect(url_for('admin_quotes'))


# ---------- admin: settings & password ----------

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('s_'):
                db.set_setting(key[2:], value.strip())
        flash('Settings saved.', 'success')
        return redirect(url_for('admin_settings'))
    settings = db.get_all_settings()
    return render_template('admin/settings.html', settings=settings)


@app.route('/admin/password', methods=['POST'])
@login_required
def admin_password():
    current = request.form.get('current') or ''
    new = request.form.get('new') or ''
    confirm = request.form.get('confirm') or ''
    if len(new) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('admin_settings'))
    if new != confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('admin_settings'))
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or not check_password_hash(user['password_hash'], current):
        conn.close()
        flash('Current password incorrect.', 'error')
        return redirect(url_for('admin_settings'))
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (generate_password_hash(new), user['id']))
    conn.commit()
    conn.close()
    flash('Password updated.', 'success')
    return redirect(url_for('admin_settings'))


# ---------- admin: FAQ ----------

@app.route('/admin/faqs', methods=['GET', 'POST'])
@login_required
def admin_faqs():
    conn = db.get_db()
    if request.method == 'POST':
        question = (request.form.get('question') or '').strip()
        answer = (request.form.get('answer') or '').strip()
        sort_order = int(request.form.get('sort_order') or 0)
        if question and answer:
            conn.execute(
                'INSERT INTO faqs (question, answer, sort_order) VALUES (?, ?, ?)',
                (question, answer, sort_order)
            )
            conn.commit()
            flash('FAQ added.', 'success')
        conn.close()
        return redirect(url_for('admin_faqs'))
    items = conn.execute('SELECT * FROM faqs ORDER BY sort_order, id').fetchall()
    conn.close()
    return render_template('admin/faqs.html', items=items)


@app.route('/admin/faqs/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_faq_delete(item_id):
    conn = db.get_db()
    conn.execute('DELETE FROM faqs WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_faqs'))


# ---------- errors ----------

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ---------- boot ----------

if __name__ == '__main__':
    if not os.path.exists(db.DB_PATH):
        print('[init] creating database & seeding sample data…')
    db.init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  Site running:  http://127.0.0.1:{port}\n  Admin login:   http://127.0.0.1:{port}/admin/login   (admin / admin123)\n')
    app.run(host='0.0.0.0', port=port, debug=True)
