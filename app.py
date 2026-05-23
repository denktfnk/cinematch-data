from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import hashlib
import urllib.parse
import requests
import re
from recommender import MovieRecommender

app = FastAPI(title="CineMatch API")
TMDB_API_KEY = "aafe4a1e99ce618b056a68fb7b415d04"

def get_tmdb_poster(title: str, bg_color: str, encoded_title: str) -> str:
    # Default placeholder
    default_url = f"https://placehold.co/300x450/{bg_color}/ffffff?text={encoded_title}"
    
    try:
        # Extract year if present, e.g., "Toy Story (1995)"
        year = ""
        clean_title = title
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = year_match.group(1)
            clean_title = title.replace(f"({year})", "").strip()
            
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={urllib.parse.quote(clean_title)}"
        if year:
            search_url += f"&year={year}"
            
        response = requests.get(search_url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                poster_path = data["results"][0].get("poster_path")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception as e:
        print(f"Error fetching poster for {title}: {e}")
        
    return default_url

# Initialize the recommender
recommender = MovieRecommender()
recommender.build_model()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/search")
async def search_movie(q: str):
    if not q:
        return {"matches": []}
    
    matches = recommender.find_movie_title(q)
    return {"matches": matches}

@app.get("/api/recommend")
async def recommend_movie(movie: str):
    if not movie:
        raise HTTPException(status_code=400, detail="Movie title is required")
    
    try:
        # Get recommendations
        recommendations = recommender.get_recommendations(movie, top_n=5)
        
        if recommendations.empty:
            return {"recommendations": [], "overlap_score": 0.0}
            
        # Evaluate recommendations
        overlap_score = recommender.evaluate_recommendations(movie, recommendations)
        
        # Convert to list of dicts for JSON response
        recs_list = recommendations.to_dict('records')
        
        # Add dynamic poster URLs
        for rec in recs_list:
            # Generate a consistent color based on title hash
            hash_hex = hashlib.md5(rec['title'].encode()).hexdigest()
            # Use only a part of the hash to ensure the color is visually pleasing (avoiding too dark/light)
            bg_color = hash_hex[:6]
            
            # Format title for placeholder (remove year if possible, but keep simple for now)
            display_title = rec['title']
            if '(' in display_title:
                display_title = display_title.split('(')[0].strip()
                
            encoded_title = urllib.parse.quote_plus(display_title)
            rec['poster_url'] = get_tmdb_poster(rec['title'], bg_color, encoded_title)
        
        return {
            "movie": movie,
            "recommendations": recs_list,
            "overlap_score": round(overlap_score, 2)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/movie_details")
async def get_movie_details(title: str):
    if not title:
        raise HTTPException(status_code=400, detail="Movie title is required")

    try:
        # Extract year and clean title
        year = ""
        clean_title = title
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = year_match.group(1)
            clean_title = title.replace(f"({year})", "").strip()

        # 1. Search for the movie to get TMDB ID
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={urllib.parse.quote(clean_title)}"
        if year:
            search_url += f"&year={year}"
            
        search_res = requests.get(search_url, timeout=5)
        search_data = search_res.json()
        
        if not search_data.get("results"):
            raise HTTPException(status_code=404, detail="Film TMDB üzerinde bulunamadı.")
            
        movie = search_data["results"][0]
        movie_id = movie["id"]
        
        # 2. Get Movie Details (score, overview)
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=tr-TR"
        details_res = requests.get(details_url, timeout=5)
        details_data = details_res.json()
        
        # 3. Get Watch Providers (TR region)
        providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
        providers_res = requests.get(providers_url, timeout=5)
        providers_data = providers_res.json()
        
        tr_providers = providers_data.get("results", {}).get("TR", {})
        
        # Extract Flatrate (Streaming) providers
        streaming_platforms = []
        if "flatrate" in tr_providers:
            streaming_platforms = [{"name": p["provider_name"], "logo": f"https://image.tmdb.org/t/p/original{p['logo_path']}"} for p in tr_providers["flatrate"]]
            
        return {
            "title": details_data.get("title", clean_title),
            "score": details_data.get("vote_average", 0),
            "overview": details_data.get("overview", "Bu film için Türkçe özet bulunmamaktadır."),
            "platforms": streaming_platforms,
            "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching details: {e}")
        raise HTTPException(status_code=500, detail="Film detayları alınırken bir hata oluştu.")
