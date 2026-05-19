# Ironclad Welding — Business Website

A complete welding-business website with admin panel. Flask + SQLite + Jinja2,
no build step, runs locally with one command.

## Features

**Public site**
- Animated welding-spark loading screen
- Square-feeling fonts: Rajdhani (headings) + Space Grotesk (body) + JetBrains Mono (accents)
- Dark / light theme toggle (persisted in localStorage, no flash on load)
- Animated hero with floating sparks
- Animated stats counter
- Services grid + per-service detail pages
- Gallery with click-to-zoom lightbox
- Testimonials section
- FAQ accordion
- Quote-request form
- Floating "Get Quote" CTA
- Toast notifications
- Mobile responsive nav
- Smooth scroll-reveal animations
- SEO: meta tags, sitemap.xml, robots.txt
- Custom 404 page

**Admin panel** (`/admin/login` · default `admin` / `admin123`)
- Dashboard with KPIs and recent quote requests
- Services: full CRUD, image upload, sort order, show/hide
- Gallery: drag-free upload (auto-resized), categorized
- Testimonials: add/delete, ratings
- Quote requests: status flow (new → contacted → won/lost)
- FAQs: add/delete
- Site settings: change branding, hero text, contact info, stats — no code edits
- Password change

## Run

```powershell
# Windows / PowerShell
py -m pip install -r requirements.txt
py app.py
```

Then open <http://127.0.0.1:5000>.

First boot creates `welding.db`, seeds 6 sample services, 4 testimonials,
5 FAQs, and the default admin user.

## First-login checklist

1. Visit <http://127.0.0.1:5000/admin/login>
2. Sign in with `admin` / `admin123`
3. Open **Settings** and change the admin password (bottom of the page)
4. Edit business name, phone, email, address, stats — everything in one place

## File layout

```
welding/
├── app.py              Flask routes (public + admin)
├── db.py               SQLite helpers + seed data
├── schema.sql          Database schema
├── requirements.txt
├── welding.db          (auto-created on first run)
├── static/
│   ├── css/style.css   Single stylesheet
│   ├── js/main.js      Theme, loader, sparks, counters, lightbox
│   ├── img/
│   └── uploads/        Admin-uploaded images land here
└── templates/
    ├── base.html       Shell: loader, nav, footer, theme system
    ├── _icons.html     Inline SVG icon macro
    ├── index.html      Home
    ├── services.html
    ├── service_detail.html
    ├── gallery.html
    ├── about.html
    ├── contact.html
    ├── 404.html
    └── admin/
        ├── _base.html     Sidebar shell
        ├── login.html
        ├── dashboard.html
        ├── services.html
        ├── service_form.html
        ├── gallery.html
        ├── testimonials.html
        ├── quotes.html
        ├── faqs.html
        └── settings.html
```

## Deploy to Render (free)

The repo includes `render.yaml`, which Render reads to auto-configure
everything. To deploy:

1. Go to <https://render.com/> and sign up (GitHub OAuth works)
2. Dashboard → **New +** → **Blueprint**
3. Connect this GitHub repo
4. Render reads `render.yaml`, sets build + start commands automatically
5. Click **Apply** — first deploy takes ~3 min
6. You get a URL like `https://mobile-welding.onrender.com`

**Heads up about free-tier data:** Render's free disk is ephemeral, so
`welding.db` and uploaded gallery images get wiped each time the service
redeploys. Fine for showing off the site; for a live business, attach a
persistent disk in the Render dashboard (~$1/mo) or switch the DB to
Render's free Postgres tier. The first request after 15 min of inactivity
also cold-starts (~30 sec) on free tier.

## Going to production (more serious)

1. Set a strong `SECRET_KEY` env var
2. Change the default admin password (do this *first*, every time)
3. Use a persistent disk or Postgres so data survives redeploys
4. Take backups of `welding.db` and `static/uploads/`
5. Add a custom domain in Render (free + auto HTTPS)

## Customising fonts

Fonts are loaded from Google Fonts in `templates/base.html`. To swap them,
change the `<link>` tag and adjust `--font-display` / body `font-family` in
`static/css/style.css`. The defaults (Rajdhani + Space Grotesk) were chosen
for their square, industrial feel while staying easy on the eyes.

## Resetting the database

Delete `welding.db` and restart — fresh seed data + default admin user.
