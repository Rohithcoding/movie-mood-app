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

# Import poster database
try:
    from movie_posters import MOVIE_POSTERS, get_poster_url
    POSTERS_AVAILABLE = True
except ImportError:
    POSTERS_AVAILABLE = False
    print("Poster database not available")

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
        
        query_lower = query.lower()
        
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
                for genre in ["Action", "Comedy", "Drama", "Romance", "Thriller"]:
                    if genre.lower() in query_lower:
                        movies = get_movies_by_genre(genre, num_recs)
                        if movies:
                            return self._format_database_movies(movies, query)
                
                # Check for specific genre keywords
                if "romance" in query_lower or "romantic" in query_lower or "love" in query_lower:
                    return self._get_romance_movies(num_recs)
                if "thriller" in query_lower or "suspense" in query_lower:
                    return self._get_thriller_movies(num_recs)
                
                # Language-based search
                for language in ["Hindi", "Tamil", "Telugu", "Malayalam", "Kannada"]:
                    if language.lower() in query_lower:
                        movies = get_movies_by_language(language, num_recs)
                        if movies:
                            return self._format_database_movies(movies, query)
                
                # Random movies as fallback
                movies = get_random_movies(num_recs)
                if movies:
                    return self._format_database_movies(movies, query)
                
            except Exception as e:
                st.warning(f"Database search failed, using basic recommendations")
        
        # Always return basic fallback to ensure recommendations are shown
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
        """Basic fallback movies - always returns recommendations"""
        basic_movies = [
            {"title": "RRR", "language": "Telugu", "year": 2022, "genres": "Action", "director": "S.S. Rajamouli", "cast": "N.T. Rama Rao Jr., Ram Charan", "rating": 8.8, "plot": "Epic action drama about two revolutionaries and their fight against British colonial rule.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Blockbuster epic with stunning visuals"},
            {"title": "KGF Chapter 2", "language": "Kannada", "year": 2022, "genres": "Action", "director": "Prashanth Neel", "cast": "Yash, Srinidhi Shetty", "rating": 8.4, "plot": "Rocky's rise to power continues as he faces new enemies and challenges.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Action-packed sequel with mass appeal"},
            {"title": "3 Idiots", "language": "Hindi", "year": 2009, "genres": "Comedy", "director": "Rajkumar Hirani", "cast": "Aamir Khan, R. Madhavan", "rating": 8.4, "plot": "Comedy about engineering students and their journey of friendship and self-discovery.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Timeless comedy with heart"},
            {"title": "Dangal", "language": "Hindi", "year": 2016, "genres": "Drama", "director": "Nitesh Tiwari", "cast": "Aamir Khan, Fatima Sana Shaikh", "rating": 8.4, "plot": "A wrestler trains his daughters to become world-class wrestlers.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Inspiring sports drama based on true story"},
            {"title": "Vikram", "language": "Tamil", "year": 2022, "genres": "Action", "director": "Lokesh Kanagaraj", "cast": "Kamal Haasan, Vijay Sethupathi", "rating": 8.4, "plot": "A special agent investigates a series of murders connected to drug cartels.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Thrilling action with stellar performances"},
            {"title": "Pushpa", "language": "Telugu", "year": 2021, "genres": "Action", "director": "Sukumar", "cast": "Allu Arjun, Rashmika Mandanna", "rating": 7.6, "plot": "A laborer rises through the ranks of a red sandalwood smuggling syndicate.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Mass entertainer with powerful performance"},
            {"title": "Baahubali 2", "language": "Telugu", "year": 2017, "genres": "Action", "director": "S.S. Rajamouli", "cast": "Prabhas, Rana Daggubati", "rating": 8.2, "plot": "The conclusion of Baahubali's epic story and the answer to why Kattappa killed Baahubali.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Epic conclusion to the legendary saga"},
            {"title": "Drishyam", "language": "Malayalam", "year": 2013, "genres": "Thriller", "director": "Jeethu Joseph", "cast": "Mohanlal, Meena", "rating": 8.3, "plot": "A man goes to great lengths to protect his family from a crime investigation.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Masterful thriller with brilliant storytelling"},
            {"title": "Kantara", "language": "Kannada", "year": 2022, "genres": "Drama", "director": "Rishab Shetty", "cast": "Rishab Shetty, Sapthami Gowda", "rating": 8.2, "plot": "A Kambala champion's conflict with an upright forest officer unfolds in this folklore drama.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Cultural masterpiece with stunning visuals"},
            {"title": "Arjun Reddy", "language": "Telugu", "year": 2017, "genres": "Drama", "director": "Sandeep Reddy Vanga", "cast": "Vijay Deverakonda, Shalini Pandey", "rating": 8.1, "plot": "A surgeon's life spirals out of control when his girlfriend marries someone else.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Intense romantic drama with raw emotions"}
        ]
        return basic_movies[:num_recs]
    
    def _get_romance_movies(self, num_recs: int) -> List[Dict]:
        """Get romance movies"""
        romance_movies = [
            {"title": "Dilwale Dulhania Le Jayenge", "language": "Hindi", "year": 1995, "genres": "Romance", "director": "Aditya Chopra", "cast": "Shah Rukh Khan, Kajol", "rating": 8.1, "plot": "A young man and woman fall in love during a trip to Europe.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Timeless romantic classic"},
            {"title": "96", "language": "Tamil", "year": 2018, "genres": "Romance", "director": "C. Prem Kumar", "cast": "Vijay Sethupathi, Trisha", "rating": 8.5, "plot": "A photographer and his high school sweetheart reconnect after 22 years.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Beautiful nostalgic love story"},
            {"title": "Geetha Govindam", "language": "Telugu", "year": 2018, "genres": "Romance", "director": "Parasuram", "cast": "Vijay Deverakonda, Rashmika Mandanna", "rating": 7.3, "plot": "A young lecturer falls for a girl but faces misunderstandings.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Sweet romantic comedy"},
            {"title": "Premam", "language": "Malayalam", "year": 2015, "genres": "Romance", "director": "Alphonse Puthren", "cast": "Nivin Pauly, Sai Pallavi", "rating": 8.3, "plot": "Three stages of love in a young man's life.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Heartwarming tale of love"},
            {"title": "Mungaru Male", "language": "Kannada", "year": 2006, "genres": "Romance", "director": "Yogaraj Bhat", "cast": "Ganesh, Pooja Gandhi", "rating": 8.2, "plot": "A young man falls in love during a train journey.", "platforms": ["Zee5"], "streaming": ["Zee5"], "why_recommended": "Kannada romantic blockbuster"}
        ]
        return romance_movies[:num_recs]
    
    def _get_thriller_movies(self, num_recs: int) -> List[Dict]:
        """Get thriller movies"""
        thriller_movies = [
            {"title": "Andhadhun", "language": "Hindi", "year": 2018, "genres": "Thriller", "director": "Sriram Raghavan", "cast": "Ayushmann Khurrana, Tabu", "rating": 8.2, "plot": "A blind pianist gets embroiled in a murder mystery.", "platforms": ["Netflix"], "streaming": ["Netflix"], "why_recommended": "Mind-bending thriller with twists"},
            {"title": "Ratsasan", "language": "Tamil", "year": 2018, "genres": "Thriller", "director": "Ram Kumar", "cast": "Vishnu Vishal, Amala Paul", "rating": 8.3, "plot": "A cop hunts a serial killer targeting school girls.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Gripping psychological thriller"},
            {"title": "Evaru", "language": "Telugu", "year": 2019, "genres": "Thriller", "director": "Venkat Ramji", "cast": "Adivi Sesh, Regina Cassandra", "rating": 7.8, "plot": "A corrupt cop investigates a rape case with shocking twists.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Intelligent crime thriller"},
            {"title": "Drishyam", "language": "Malayalam", "year": 2013, "genres": "Thriller", "director": "Jeethu Joseph", "cast": "Mohanlal, Meena", "rating": 8.3, "plot": "A man protects his family from a murder investigation.", "platforms": ["Hotstar"], "streaming": ["Hotstar"], "why_recommended": "Masterful family thriller"},
            {"title": "U Turn", "language": "Kannada", "year": 2016, "genres": "Thriller", "director": "Pawan Kumar", "cast": "Shraddha Srinath, Roger Narayan", "rating": 7.4, "plot": "A journalist investigates accidents at a flyover.", "platforms": ["Prime Video"], "streaming": ["Prime Video"], "why_recommended": "Supernatural thriller with social message"}
        ]
        return thriller_movies[:num_recs]

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

def get_movie_poster_url(movie_title: str, year: int) -> str:
    """Get movie poster URL with comprehensive database and API fallback"""
    
    # First check comprehensive poster database
    if POSTERS_AVAILABLE:
        try:
            poster_url = get_poster_url(movie_title)
            if poster_url:
                return poster_url
        except Exception as e:
            print(f"Poster database error for {movie_title}: {e}")
    
    # Hardcoded popular movie posters as backup
    popular_posters = {
        "RRR": "https://m.media-amazon.com/images/M/MV5BODUwNDNjYzctODUxNy00ZTA2LWIyYTEtMDc5Y2E5ZjBmNTMzXkEyXkFqcGdeQXVyODE5NzE3OTE@._V1_SX300.jpg",
        "KGF Chapter 2": "https://m.media-amazon.com/images/M/MV5BZWNiOTc4NGItNGY4NC00ZTdkLTlkOTEtNDE2YzZiNGRkNTFhXkEyXkFqcGdeQXVyMTI1NDEyNTM5._V1_SX300.jpg",
        "3 Idiots": "https://m.media-amazon.com/images/M/MV5BNTkyOGVjMGEtNmQzZi00NzFlLTlhOWQtODYyMDc2ZGJmYzFhXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
        "Dangal": "https://m.media-amazon.com/images/M/MV5BMTQ4MzQzMzM2Nl5BMl5BanBnXkFtZTgwMTQ1NzU3MDI@._V1_SX300.jpg",
        "Vikram": "https://m.media-amazon.com/images/M/MV5BYjFjMTQzY2EtZjQ5MC00NGUyLWJiYWMtZDI3MTQ1MGU4OGY2XkEyXkFqcGdeQXVyNDExMjcyMzA@._V1_SX300.jpg",
        "Pushpa": "https://m.media-amazon.com/images/M/MV5BNGZlNTFlOWMtMzUwNC00ZDdhLWI4Y2UtYTY2ZDhmMGQ0OTc1XkEyXkFqcGdeQXVyMTI1NDEyNTM5._V1_SX300.jpg",
        "Baahubali 2": "https://m.media-amazon.com/images/M/MV5BYTMxMGY2ZjQtYjdmOS00NzlkLWJiMjItZGM0MWY3MmQ1NjM2XkEyXkFqcGdeQXVyMzc5Mjk3OA@@._V1_SX300.jpg",
        "Drishyam": "https://m.media-amazon.com/images/M/MV5BYjY2NGNmYjQtZjg5MC00NGVmLWJkZTgtMzQ3YzgyNTY2YTVkXkEyXkFqcGdeQXVyMjkxNzQ1NDI@._V1_SX300.jpg",
        "Kantara": "https://m.media-amazon.com/images/M/MV5BM2Q3MWEwM2EtNzQwZC00YzE0LWJlYWYtMjk1ZjNlYWQ3ZTQyXkEyXkFqcGdeQXVyMTUzNTgzNzM0._V1_SX300.jpg",
        "Arjun Reddy": "https://m.media-amazon.com/images/M/MV5BNzIwMzk1MjEtZGUxZi00YTMwLWFiYWMtZDI2Yjk0NzlmMmE2XkEyXkFqcGdeQXVyMzgxODM4NjM@._V1_SX300.jpg"
    }
    
    if movie_title in popular_posters:
        return popular_posters[movie_title]
    
    # Then try OMDB API
    try:
        omdb_url = f"https://www.omdbapi.com/?t={movie_title}&y={year}&apikey=7f7c782e-0051-449b-8636-94d0a0719c05"
        response = requests.get(omdb_url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('Poster') and data['Poster'] != 'N/A':
                return data['Poster']
    except:
        pass
    
    # Return None for gradient card fallback
    return None

def display_movie_card(movie: Dict):
    """Display a movie recommendation card with poster and clickable platform links"""
    platforms = movie.get('platforms', movie.get('streaming', ['Netflix']))
    
    # Get movie poster
    poster_url = get_movie_poster_url(movie['title'], movie['year'])
    
    # Create clickable platform badges
    platform_badges = []
    for platform in platforms:
        url = get_platform_url(platform, movie['title'])
        platform_badges.append(f'<a href="{url}" target="_blank" style="text-decoration: none;"><span class="platform-badge" style="cursor: pointer; transition: all 0.3s ease; background: rgba(255,255,255,0.3);" onmouseover="this.style.background=\'rgba(255,255,255,0.5)\'" onmouseout="this.style.background=\'rgba(255,255,255,0.3)\'">{platform}</span></a>')
    
    platform_badges_html = ''.join(platform_badges)
    
    # Create two-column layout with poster and details
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display movie poster or gradient card
        if poster_url:
            try:
                st.image(poster_url, width=200, caption=f"{movie['title']} ({movie['year']})")
            except Exception as e:
                # Show gradient card if image fails to load
                st.markdown(f"""
                <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 1.5rem; border-radius: 15px; height: 280px; width: 200px;
                            display: flex; align-items: center; justify-content: center; margin: 0 auto;
                            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🎬</div>
                        <h4 style="margin: 0.5rem 0; font-size: 1.1rem;">{movie['title']}</h4>
                        <p style="margin: 0; opacity: 0.8;">({movie['year']})</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Show gradient card for movies without posters
            st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 1.5rem; border-radius: 15px; height: 280px; width: 200px;
                        display: flex; align-items: center; justify-content: center; margin: 0 auto;
                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎬</div>
                    <h4 style="margin: 0.5rem 0; font-size: 1.1rem;">{movie['title']}</h4>
                    <p style="margin: 0; opacity: 0.8;">({movie['year']})</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Display movie details
        st.markdown(f"""
        <div class="movie-card" style="margin: 0;">
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
    
    # Initialize recommender
    recommender = MovieRecommender()
    
    # Browse by Categories Section
    st.markdown("## 🎭 Browse by Categories")
    
    # Popular Genres Section
    st.markdown("### 🎬 Popular Genres")
    genre_cols = st.columns(5)
    
    query = ""
    
    with genre_cols[0]:
        if st.button("🎬 Action", use_container_width=True):
            query = "action movies"
    with genre_cols[1]:
        if st.button("😂 Comedy", use_container_width=True):
            query = "comedy movies"
    with genre_cols[2]:
        if st.button("💔 Drama", use_container_width=True):
            query = "drama movies"
    with genre_cols[3]:
        if st.button("❤️ Romance", use_container_width=True):
            query = "romance movies"
    with genre_cols[4]:
        if st.button("🔥 Thriller", use_container_width=True):
            query = "thriller movies"
    
    # Languages Section
    st.markdown("### 🌍 Languages")
    lang_cols = st.columns(5)
    
    with lang_cols[0]:
        if st.button("🇮🇳 Hindi", use_container_width=True):
            query = "hindi movies"
    with lang_cols[1]:
        if st.button("🎭 Tamil", use_container_width=True):
            query = "tamil movies"
    with lang_cols[2]:
        if st.button("🎪 Telugu", use_container_width=True):
            query = "telugu movies"
    with lang_cols[3]:
        if st.button("🌴 Malayalam", use_container_width=True):
            query = "malayalam movies"
    with lang_cols[4]:
        if st.button("🎨 Kannada", use_container_width=True):
            query = "kannada movies"
    
    st.markdown("---")
    
    # AI Search Section
    st.markdown("## 🔍 Ask AI for Movie Recommendations")
    st.markdown("### What kind of movies are you looking for?")
    
    # Search input
    search_query = st.text_input(
        "Search Movies",
        placeholder="e.g., 'Tamil action movies', 'Hindi comedy films', 'Malayalam thrillers', 'latest Bollywood'",
        key="movie_search",
        label_visibility="collapsed"
    )
    
    # Use search query if entered, otherwise use button query
    if search_query:
        query = search_query
    
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
