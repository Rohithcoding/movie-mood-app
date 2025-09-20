"""
AI-Powered Movie Recommendation System with Comprehensive Database
Features 200+ movies per genre and language
"""

import streamlit as st
import requests
import json
import random
from typing import List, Dict

# Try to import comprehensive database, fallback if not available
try:
    from movie_database_generator import (
        COMPREHENSIVE_MOVIE_DATABASE, 
        GENRE_INDEX, 
        LANGUAGE_INDEX,
        get_movies_by_genre,
        get_movies_by_language,
        search_movies,
        get_random_movies
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Comprehensive database not available, using basic fallback")

# Configure Streamlit page
st.set_page_config(
    page_title="🎬 Movie Mood",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #667eea;
        font-size: 4rem;
        font-weight: 800;
        margin: 2rem 0;
        text-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .movie-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .movie-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .movie-details {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0.3rem 0;
    }
    .platform-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    .search-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

class MovieRecommender:
    def __init__(self):
        self.omdb_api_key = "7f7c782e-0051-449b-8636-94d0a0719c05"
        
        # Get OpenAI API key from Streamlit secrets
        try:
            self.openai_api_key = st.secrets["OPENAI_API_KEY"]
        except:
            # For deployment, set your API key in Streamlit Cloud secrets
            self.openai_api_key = ""
        
        # Configure OpenAI API
        self.openai_available = self._test_openai_api() if self.openai_api_key else False
        self.ai_available = True
    
    def _test_openai_api(self) -> bool:
        """Test if OpenAI API is working"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except:
            return False
    
    def generate_ai_recommendations(self, query: str, num_recs: int = 5) -> List[Dict]:
        """Generate movie recommendations using OpenAI or comprehensive database"""
        
        if self.openai_available:
            return self._openai_recommendations(query, num_recs)
        else:
            return self._comprehensive_database_recommendations(query, num_recs)
    
    def _openai_recommendations(self, query: str, num_recs: int) -> List[Dict]:
        """Use OpenAI GPT for real-time movie recommendations"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""You are an expert Indian cinema AI. Based on the query "{query}", provide {num_recs} real Indian movie recommendations.

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Actual Movie Title",
    "language": "Hindi/Tamil/Telugu/Malayalam/Kannada",
    "year": 2020,
    "genres": "Action,Drama",
    "director": "Real Director Name",
    "cast": "Actor 1, Actor 2",
    "rating": 8.2,
    "plot": "Actual plot summary",
    "platforms": ["Netflix", "Prime Video"],
    "why_recommended": "Reason for recommendation"
  }}
]

Focus on real, popular Indian movies. Return ONLY the JSON array."""
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Indian cinema AI. Always respond with valid JSON arrays only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 3000,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    movies_json = content.strip()
                    if movies_json.startswith('```json'):
                        movies_json = movies_json.replace('```json', '').replace('```', '')
                    if movies_json.startswith('```'):
                        movies_json = movies_json.replace('```', '')
                    
                    movies = json.loads(movies_json)
                    
                    # Ensure proper format
                    for movie in movies:
                        if 'platforms' not in movie:
                            movie['platforms'] = ["Netflix"]
                        movie['streaming'] = movie['platforms']
                    
                    return movies
                    
                except json.JSONDecodeError:
                    st.warning("OpenAI response parsing failed. Using comprehensive database.")
                    return self._comprehensive_database_recommendations(query, num_recs)
            else:
                st.warning("OpenAI API issue. Using comprehensive database.")
                return self._comprehensive_database_recommendations(query, num_recs)
                
        except Exception as e:
            st.warning("OpenAI error. Using comprehensive database.")
            return self._comprehensive_database_recommendations(query, num_recs)
    
    def _comprehensive_database_recommendations(self, query: str, num_recs: int) -> List[Dict]:
        """Use comprehensive database with 200+ movies per genre/language"""
        
        if DATABASE_AVAILABLE:
            try:
                # Search in comprehensive database
                search_results = search_movies(query, limit=num_recs * 2)
                
                if search_results:
                    recommendations = []
                    for movie in search_results[:num_recs]:
                        formatted_movie = {
                            "title": movie["title"],
                            "language": movie["language"],
                            "year": movie["year"],
                            "genres": movie["genre"],
                            "director": movie["director"],
                            "cast": movie["cast"],
                            "rating": movie["rating"],
                            "plot": movie["plot"],
                            "platforms": [movie["watch_on"]],
                            "streaming": [movie["watch_on"]],
                            "why_recommended": f"From comprehensive database: {movie['genre']} {movie['language']} cinema"
                        }
                        recommendations.append(formatted_movie)
                    return recommendations
                
                # Genre-based search
                query_lower = query.lower()
                for genre in ["Action", "Comedy", "Drama", "Romance", "Thriller"]:
                    if genre.lower() in query_lower:
                        movies = get_movies_by_genre(genre, num_recs)
                        return self._format_database_movies(movies, query)
                
                # Language-based search
                for language in ["Hindi", "Tamil", "Telugu", "Malayalam", "Kannada"]:
                    if language.lower() in query_lower:
                        movies = get_movies_by_language(language, num_recs)
                        return self._format_database_movies(movies, query)
                
                # Random movies
                movies = get_random_movies(num_recs)
                return self._format_database_movies(movies, query)
                
            except Exception as e:
                st.error(f"Database error: {str(e)}")
        
        # Basic fallback
        return self._basic_fallback_movies(num_recs)
    
    def _format_database_movies(self, movies: List[Dict], query: str) -> List[Dict]:
        """Format database movies"""
        formatted = []
        for movie in movies:
            formatted_movie = {
                "title": movie["title"],
                "language": movie["language"],
                "year": movie["year"],
                "genres": movie["genre"],
                "director": movie["director"],
                "cast": movie["cast"],
                "rating": movie["rating"],
                "plot": movie["plot"],
                "platforms": [movie["watch_on"]],
                "streaming": [movie["watch_on"]],
                "why_recommended": f"Great {movie['genre']} movie"
            }
            formatted.append(formatted_movie)
        return formatted
    
    def _basic_fallback_movies(self, num_recs: int) -> List[Dict]:
        """Basic fallback movies"""
        basic_movies = [
            {"title": "RRR", "language": "Telugu", "year": 2022, "genres": "Action", "director": "S.S. Rajamouli", "cast": "N.T. Rama Rao Jr., Ram Charan", "rating": 8.8, "plot": "Epic action drama about two revolutionaries.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Blockbuster epic"},
            {"title": "KGF Chapter 2", "language": "Kannada", "year": 2022, "genres": "Action", "director": "Prashanth Neel", "cast": "Yash, Srinidhi Shetty", "rating": 8.4, "plot": "Rocky's rise to power continues.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Action blockbuster"},
            {"title": "3 Idiots", "language": "Hindi", "year": 2009, "genres": "Comedy", "director": "Rajkumar Hirani", "cast": "Aamir Khan, R. Madhavan", "rating": 8.4, "plot": "Comedy about engineering students.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Classic comedy"},
            {"title": "Dangal", "language": "Hindi", "year": 2016, "genres": "Drama", "director": "Nitesh Tiwari", "cast": "Aamir Khan, Fatima Sana Shaikh", "rating": 8.4, "plot": "Wrestler trains his daughters.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Inspiring sports drama"},
            {"title": "Vikram", "language": "Tamil", "year": 2022, "genres": "Action", "director": "Lokesh Kanagaraj", "cast": "Kamal Haasan, Vijay Sethupathi", "rating": 8.4, "plot": "Special agent investigates murders.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Thrilling action"}
        ]
        return basic_movies[:num_recs]

def get_platform_url(platform: str, movie_title: str) -> str:
    """Get direct URL to streaming platform"""
    platform_urls = {
        "Netflix": "https://www.netflix.com/search?q=",
        "Prime Video": "https://www.primevideo.com/search/ref=atv_nb_sr?phrase=",
        "Hotstar": "https://www.hotstar.com/in/search?q=",
        "Zee5": "https://www.zee5.com/search?q=",
        "YouTube": "https://www.youtube.com/results?search_query="
    }
    
    base_url = platform_urls.get(platform, "https://www.google.com/search?q=")
    search_query = movie_title.replace(" ", "+")
    return f"{base_url}{search_query}"

def display_movie_card(movie: Dict):
    """Display a movie recommendation card with clickable platform links"""
    platforms = movie.get('platforms', movie.get('streaming', ['Netflix']))
    
    # Create clickable platform badges
    platform_badges = []
    for platform in platforms:
        url = get_platform_url(platform, movie['title'])
        platform_badges.append(f'<a href="{url}" target="_blank" style="text-decoration: none;"><span class="platform-badge" style="cursor: pointer; transition: all 0.3s ease; background: rgba(255,255,255,0.3);" onmouseover="this.style.background=\'rgba(255,255,255,0.5)\'" onmouseout="this.style.background=\'rgba(255,255,255,0.3)\'">{platform}</span></a>')
    
    platform_badges_html = ''.join(platform_badges)
    
    st.markdown(f"""
    <div class="movie-card">
        <div class="movie-title">{movie['title']}</div>
        <div class="movie-details">
            <strong>{movie['language']}</strong> • {movie['year']} • ⭐ {movie['rating']}/10
        </div>
        <div class="movie-details">
            <strong>Genre:</strong> {movie['genres']} | <strong>Director:</strong> {movie['director']}
        </div>
        <div class="movie-details">
            <strong>Cast:</strong> {movie['cast']}
        </div>
        <div class="movie-details" style="margin: 1rem 0;">
            {movie['plot']}
        </div>
        <div class="movie-details">
            <strong>Why recommended:</strong> {movie.get('why_recommended', 'Great movie choice!')}
        </div>
        <div style="margin-top: 1rem;">
            <strong>Watch on:</strong> {platform_badges_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 Movie Mood</h1>', unsafe_allow_html=True)
    
    # Database status (hidden from user interface)
    
    # Initialize recommender
    recommender = MovieRecommender()
    
    # Search interface
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.markdown("### 🔍 What kind of movie are you in the mood for?")
    
    # Search input
    query = st.text_input(
        "Search Movies",
        placeholder="e.g., 'Tamil action movies', 'Hindi comedy films', 'Malayalam thrillers', 'latest Bollywood'",
        key="movie_search",
        label_visibility="collapsed"
    )
    
    # Quick filters
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎬 Latest Blockbusters"):
            query = "latest blockbuster movies 2023 2024"
    with col2:
        if st.button("😂 Comedy Movies"):
            query = "comedy movies funny films"
    with col3:
        if st.button("🔥 Action Thrillers"):
            query = "action thriller movies"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate recommendations
    if query:
        with st.spinner("🎭 Finding perfect movies for you..."):
            try:
                recommendations = recommender.generate_ai_recommendations(query, 5)
                
                if recommendations:
                    st.markdown("### 🎯 Perfect Matches for You:")
                    
                    for movie in recommendations:
                        display_movie_card(movie)
                else:
                    st.error("No recommendations found. Try a different search term.")
                    
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")
                st.info("Try refreshing the page or using different search terms.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin: 2rem 0;">
        <p>🎬 Movie Mood - Your AI-Powered Movie Companion</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
