import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'welding.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    seed(conn)
    conn.close()


def seed(conn):
    cur = conn.cursor()

    # Default admin (CHANGE PASSWORD AFTER FIRST LOGIN)
    cur.execute('SELECT COUNT(*) FROM users')
    if cur.fetchone()[0] == 0:
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            ('admin', generate_password_hash('admin123'))
        )

    # Default settings — MOBILE WELDING focus
    defaults = {
        'business_name': 'Ironclad Mobile Welding',
        'tagline': 'Mobile welding. Anywhere. Anytime.',
        'phone': '(555) 012-3456',
        'email': 'dispatch@ironcladmobile.example',
        'address': 'Serving the metro area — we come to you',
        'hours': '24/7 Emergency · Same-day quotes',
        'hero_title': 'Mobile Welding · Anywhere You Need It',
        'hero_subtitle': 'Fully-equipped service truck, certified welders, on your job site within hours. Steel, stainless, aluminum — all processes, all materials, all on location.',
        'about_text': 'We are a fully mobile welding operation. No drop-off, no waiting, no shop visits — we bring the truck, the generator, the gas, and the experience to wherever the work is.\n\nFrom busted trailer hitches at the side of the road to structural welds on a construction site, every job gets the same standard: certified welder, signed work, lifetime workmanship guarantee.',
        'service_radius_miles': '75',
        'response_time': '90 min',
        'projects_completed': '1100',
        'happy_clients': '850',
        'rating': '5.0',
        'instagram_url': '',
        'facebook_url': '',
    }
    for k, v in defaults.items():
        cur.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))

    # Sample services — MOBILE only
    cur.execute('SELECT COUNT(*) FROM services')
    if cur.fetchone()[0] == 0:
        services = [
            ('24/7 Emergency Mobile Welding', 'emergency', 'Trailer broken? Gate fell off? Equipment down? We roll out — day or night.',
             'When the job can\'t wait, we don\'t make you. Same-day dispatch across the metro area, 24/7 for true emergencies. Service truck carries MIG, TIG, and Stick setups plus a 5kW generator — no power, no problem.',
             'bolt', 'from $185 + travel', None, 10),
            ('Trailer & Hitch Repair', 'trailer-hitch', 'Frame cracks, broken hitches, busted gates, snapped supports — fixed on site.',
             'Trailer welding is our bread and butter. Whether it\'s a flatbed frame, a tongue, a hitch, a ramp gate, or a stake pocket, we weld it right and you keep working. Most jobs done in 1–2 hours.',
             'truck', 'from $150 + travel', None, 20),
            ('Heavy Equipment On-Site', 'heavy-equipment', 'Bucket cracks, frame welds, structural repairs — we come to the machine.',
             'Excavators, skid steers, loaders, dump bodies, attachments. We bring the truck, the gas, and the welder rated for the steel grade. Downtime is expensive — we minimize it.',
             'hammer', 'from $200 + travel', None, 30),
            ('Gate, Fence & Railing', 'gates-fences', 'Driveway gates, security fencing, handrails — repaired or installed on location.',
             'Wrought iron, chain-link top rails, steel gates, automatic gate hinges, balcony railings. Fabricated and welded right where they\'ll live, so it fits the first time.',
             'shield', 'from $145 + travel', None, 40),
            ('Aluminum & Marine Repair', 'aluminum-marine', 'TIG-quality aluminum welding on boats, RVs, ladders — at your dock or driveway.',
             'Cracked aluminum boat transoms, RV step assemblies, marine railings, fuel tanks. Pure argon, AC TIG, no shortcuts. Aluminum is unforgiving and we treat it that way.',
             'target', 'from $175 + travel', None, 50),
            ('Farm & Agricultural', 'farm', 'Implements, gates, livestock equipment, grain bins — fixed where the work is.',
             'Tractors don\'t fit in a welding shop. We come out to the barn, the field, or the lot. Plows, augers, headers, cattle chutes, feeders, hitch plates — all welded in place.',
             'wrench', 'from $165 + travel', None, 60),
        ]
        cur.executemany(
            'INSERT INTO services (title, slug, short_desc, long_desc, icon, price_from, image, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            services
        )

    # Sample testimonials — mobile focused
    cur.execute('SELECT COUNT(*) FROM testimonials')
    if cur.fetchone()[0] == 0:
        testimonials = [
            ('Marcus Trenholm', 'General Contractor', 'Called at 7am with a cracked excavator bucket. They were on site by 9. Back to work by lunch. That kind of response is gold on a job site.', 5),
            ('Sara Okafor', 'Trailer Rental Owner', 'Three trailers down in a week — different problems each time. They came to our yard, fixed everything, didn\'t make us tow anything. Saved us thousands.', 5),
            ('Dan Reilly', 'Homeowner', 'My driveway gate hinge sheared off Sunday morning. They came out the same day, welded it stronger than new. Polite, fast, fair price.', 5),
            ('Priya Anand', 'Farm Manager', 'They\'ve become our go-to. Plow welds, gate repairs, feeder fixes — they show up, weld it once, weld it right. No second trips.', 5),
        ]
        cur.executemany(
            'INSERT INTO testimonials (author, role, body, rating) VALUES (?, ?, ?, ?)',
            testimonials
        )

    # FAQs — mobile focused
    cur.execute('SELECT COUNT(*) FROM faqs')
    if cur.fetchone()[0] == 0:
        faqs = [
            ('How far do you travel?', '75 miles from the metro area is standard, included in the trip rate. Beyond that we travel anywhere — additional mileage billed at $1/mi each way.', 10),
            ('How fast can you get to me?', 'For true emergencies, typically 60–120 minutes inside the service radius. Scheduled jobs are usually next-day or same-week.', 20),
            ('What can you weld on-site?', 'Carbon steel, stainless, aluminum, cast iron, and most exotic alloys. We run MIG, TIG, and Stick from the truck — same quality as a shop, just in your driveway.', 30),
            ('Do you bring your own power?', 'Yes — the truck has a 5kW generator and a full set of gas cylinders. We only need access. No power, no gas, no problem.', 40),
            ('Are you certified and insured?', 'AWS D1.1 certified for structural steel, $2M general liability insurance, and bonded. Certificates available on request.', 50),
            ('How does pricing work?', 'A flat trip charge plus an hourly rate. We quote the trip charge before dispatching so there are no surprises. Most repairs are 1–3 hours of welding on site.', 60),
            ('Do you guarantee the work?', 'Lifetime workmanship guarantee. If a joint we welded ever fails under normal use, we come back and re-weld it — free.', 70),
        ]
        cur.executemany(
            'INSERT INTO faqs (question, answer, sort_order) VALUES (?, ?, ?)',
            faqs
        )

    conn.commit()


def get_setting(key, default=''):
    conn = get_db()
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def get_all_settings():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        'INSERT INTO settings (key, value) VALUES (?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
        (key, value)
    )
    conn.commit()
    conn.close()
