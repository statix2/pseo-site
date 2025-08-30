#!/usr/bin/env python3
import csv, json, os, re, html, urllib.request, pathlib, time
from datetime import datetime

def slugify(s):
    s = s.lower()
    s = re.sub(r"[àáâä]", "a", s)
    s = re.sub(r"[èéêë]", "e", s)
    s = re.sub(r"[ìíîï]", "i", s)
    s = re.sub(r"[òóôö]", "o", s)
    s = re.sub(r"[ùúûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "x"

ROOT = pathlib.Path(__file__).parent.resolve()
with open(ROOT / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

OUT = ROOT / CONFIG["build"]["output_dir"]
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"

for p in [OUT, OUT/"assets"]:
    os.makedirs(p, exist_ok=True)

# Copy assets
import shutil
shutil.copy2(ASSETS / "style.css", OUT / "assets" / "style.css")

# Load templates
base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
tpl_index = (TEMPLATES / "index.html").read_text(encoding="utf-8")
tpl_city = (TEMPLATES / "city.html").read_text(encoding="utf-8")
tpl_page = (TEMPLATES / "page.html").read_text(encoding="utf-8")

# Fetch CSV
rows = []
src = ROOT / "data" / "points.csv"
csv_url = CONFIG.get("sheet_csv_url","").strip()
try:
    if csv_url and "http" in csv_url:
        with urllib.request.urlopen(csv_url, timeout=20) as r:
            data = r.read().decode("utf-8")
        # Save a copy for debug
        (ROOT / "data").mkdir(exist_ok=True, parents=True)
        (ROOT / "data" / "points_fetched.csv").write_text(data, encoding="utf-8")
        src = ROOT / "data" / "points_fetched.csv"
except Exception as e:
    print("Impossible de récupérer le CSV distant, utilisation du CSV local. Raison:", e)

with open(src, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        r = {k.strip(): (v or "").strip() for k,v in r.items()}
        if not r.get("name"):
            continue
        rows.append(r)

# Group by city
by_city = {}
for r in rows:
    city = r.get("city","").strip() or "Ville"
    by_city.setdefault(city, []).append(r)

def render_base(title, desc, content, canonical=""):
    html_out = base
    html_out = html_out.replace("{{PAGE_TITLE}}", html.escape(title))
    html_out = html_out.replace("{{PAGE_DESC}}", html.escape(desc))
    base_path = "."  # will be corrected per page
    html_out = html_out.replace("{{BASE_PATH}}", "{{BASE_PATH}}")  # placeholder
    html_out = html_out.replace("{{CANONICAL}}", canonical or "")
    html_out = html_out.replace("{{SITE_NAME}}", CONFIG["site_name"])
    html_out = html_out.replace("{{YEAR}}", str(datetime.now().year))
    html_out = html_out.replace("{{CONTENT}}", content)
    return html_out

def aff_block():
    tag = (CONFIG.get("affiliate") or {}).get("amazon_tag","").strip()
    kw = (CONFIG.get("affiliate") or {}).get("keywords", [])
    if not tag or not kw:
        return ""
    links = []
    for k in kw:
        q = urllib.parse.quote(k)
        url = f"https://www.amazon.fr/s?k={q}&tag={tag}"
        links.append(f'<a href="{url}" rel="nofollow sponsored noopener" target="_blank">Voir {html.escape(k)}</a>')
    return f'<div class="aff"><div class="tag">Suggestions utiles</div>{"".join(links)}</div>'

# Generate city pages and item pages
all_pages = []

for city, items in sorted(by_city.items(), key=lambda kv: kv[0].lower()):
    city_slug = slugify(city)
    city_dir = OUT / city_slug
    city_dir.mkdir(parents=True, exist_ok=True)

    cards = []
    for r in items:
        name = r.get("name","")
        name_slug = slugify(name)
        page_rel = f"{name_slug}.html"
        page_path = city_dir / page_rel
        address = r.get("address","")
        hours = r.get("hours","")
        feats = [x.strip() for x in (r.get("features","").split(";")) if x.strip()]
        feats_sentence = ", ".join(feats) if feats else "voir sur place"
        photo = r.get("photo_url","")
        website = r.get("website_url","")

        # Page content
        page_inner = tpl_page
        page_inner = page_inner.replace("{{TYPE_LABEL}}", CONFIG["niche"]["type_label"])
        page_inner = page_inner.replace("{{TYPE_LABEL_LOWER}}", CONFIG["niche"]["type_label"].lower())
        page_inner = page_inner.replace("{{NAME}}", html.escape(name))
        page_inner = page_inner.replace("{{CITY}}", html.escape(city))
        page_inner = page_inner.replace("{{ADDRESS}}", html.escape(address))
        page_inner = page_inner.replace("{{HOURS}}", html.escape(hours or "horaires variables"))
        page_inner = page_inner.replace("{{FEATURES_SENTENCE}}", html.escape(feats_sentence))
        page_inner = page_inner.replace("{{PHOTO_URL}}", html.escape(photo))
        page_inner = page_inner.replace("{{WEBSITE_URL}}", html.escape(website or "#"))
        page_inner = page_inner.replace("{{LAT}}", html.escape(r.get("lat","")))
        page_inner = page_inner.replace("{{LON}}", html.escape(r.get("lon","")))
        page_inner = page_inner.replace("{{AFF_BLOCK}}", aff_block())

        title = f"{CONFIG['niche']['type_label']} à {city} – {name}"
        desc = f"{CONFIG['niche']['type_label']} {name} à {city}. Adresse: {address}. Horaires: {hours or 'variables'}."
        page_html_full = render_base(title, desc, page_inner, canonical=f"{CONFIG['base_url'].rstrip('/')}/{city_slug}/{name_slug}.html")
        # Fix base path
        page_html_full = page_html_full.replace("{{BASE_PATH}}", "..")
        page_path.write_text(page_html_full, encoding="utf-8")
        all_pages.append(f"/{city_slug}/{name_slug}.html")

        # Card for city listing
        img = f'<img src="{html.escape(photo)}" alt="{html.escape(name)}">'
        card = f'''<a class="card" href="./{name_slug}.html">{img}<div class="p"><div style="font-weight:600">{html.escape(name)}</div><div class="meta">{html.escape(address)}</div></div></a>'''
        cards.append(card)

    # City index
    city_inner = tpl_city
    city_inner = city_inner.replace("{{PLURAL_LABEL}}", CONFIG["niche"]["plural_label"])
    city_inner = city_inner.replace("{{CITY}}", html.escape(city))
    city_inner = city_inner.replace("{{COUNT}}", str(len(items)))
    city_inner = city_inner.replace("{{CARDS}}", "\n".join(cards))
    title = f"{CONFIG['niche']['plural_label']} à {city}"
    desc = f"{CONFIG['niche']['plural_label']} à {city} : {len(items)} lieux."
    city_html_full = render_base(title, desc, city_inner, canonical=f"{CONFIG['base_url'].rstrip('/')}/{city_slug}/index.html")
    city_html_full = city_html_full.replace("{{BASE_PATH}}", "..")
    (city_dir / "index.html").write_text(city_html_full, encoding="utf-8")
    all_pages.append(f"/{city_slug}/index.html")

# Home with city cards
city_cards = []
for city, items in sorted(by_city.items(), key=lambda kv: kv[0].lower()):
    city_slug = slugify(city)
    count = len(items)
    first_photo = ""
    for r in items:
        if r.get("photo_url"):
            first_photo = r["photo_url"]
            break
    img = f'<img src="{html.escape(first_photo)}" alt="{html.escape(city)}">' if first_photo else ""
    card = f'''<a class="card" href="./{city_slug}/index.html">{img}<div class="p"><div style="font-weight:700">{html.escape(city)}</div><div class="meta">{count} lieux</div></div></a>'''
    city_cards.append(card)

home_inner = tpl_index.replace("{{CITY_CARDS}}", "\n".join(city_cards)).replace("{{TYPE_LABEL}}", CONFIG["niche"]["type_label"])
home_html = render_base(CONFIG["site_name"], f"Répertoire des {CONFIG['niche']['plural_label']}.", home_inner, canonical=f"{CONFIG['base_url'].rstrip('/')}/index.html")
home_html = home_html.replace("{{BASE_PATH}}", ".")
(OUT / "index.html").write_text(home_html, encoding="utf-8")
all_pages.append("/index.html")

# robots.txt & sitemap.xml
(OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: {}/sitemap.xml\n".format(CONFIG["base_url"].rstrip("/")), encoding="utf-8")

sitemap_urls = "\n".join([f"<url><loc>{CONFIG['base_url'].rstrip('/')}{html.escape(p)}</loc><changefreq>weekly</changefreq></url>" for p in all_pages])
sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap_urls}\n</urlset>\n'
(OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

print("Build terminé. Fichiers dans:", OUT)
