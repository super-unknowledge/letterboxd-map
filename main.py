import feedparser
import requests
import re
import time
import os
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd
import pycountry

load_dotenv()

# === CONFIGURATION ===
LETTERBOXD_USERNAME = os.getenv("LETTERBOXD_USERNAME")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
MAX_FILMS = 3  # Limit number of films for demo (set None for unlimited)

if not LETTERBOXD_USERNAME or not TMDB_API_KEY:
    raise ValueError("Missing LETTERBOXD_USERNAME or TMDB_API_KEY in .env file")

# === STEP 1: Parse RSS feed ===
rss_url = f"https://letterboxd.com/{LETTERBOXD_USERNAME}/rss/"
feed = feedparser.parse(rss_url)

# === STEP 2: Extract watched film titles ===
def extract_film_title(entry):
    return entry.get("letterboxd_filmtitle")
film_titles = []
for entry in feed.entries:
    title = extract_film_title(entry)
    if title and title not in film_titles:
        film_titles.append(title)
    if MAX_FILMS and len(film_titles) >= MAX_FILMS:
        break

# === STEP 3: Query TMDB API for country info ===
def get_country_for_film(title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    details_url = "https://api.themoviedb.org/3/movie/{}"

    # Search for the movie
    params = {"api_key": TMDB_API_KEY, "query": title}
    r = requests.get(search_url, params=params)
    results = r.json().get("results", [])
    if not results:
        return None

    # Get movie details
    movie_id = results[0]["id"]
    r = requests.get(details_url.format(movie_id), params={"api_key": TMDB_API_KEY})
    data = r.json()
    countries = data.get("origin_country", [])

    return [c for c in countries] if countries else ["Unknown"]

# === STEP 4: Print film list with countries ===
print(f"Watched films for: {LETTERBOXD_USERNAME}\n")

for title in film_titles:
    try:
        countries = get_country_for_film(title)
        print(f"{title} — {', '.join(countries)}")
        time.sleep(0.5)  # Be polite to TMDB servers
    except Exception as e:
        print(f"{title} — [Error: {e}]")

# === Step 2: Convert country names to ISO Alpha-3 codes ===
# All ISO country codes for reference
all_countries = [country.name for country in pycountry.countries]
country_data = []

for country_name in all_countries:
    if iso3:
        watched = country_name in watched_countries
        country_data.append({
            "country": country_name,
            "iso_alpha": iso3,
            "watched": watched
        })

df = pd.DataFrame(country_data)

# === Step 3: Plot with Plotly ===
fig = px.choropleth(
    df,
    locations="iso_alpha",
    color="watched",
    hover_name="country",
    color_discrete_map={True: "red", False: "lightgray"},
    title="Countries of Origin for Watched Films"
)

fig.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type="natural earth"
    ),
)

fig.show()
