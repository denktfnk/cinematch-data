import streamlit as st
from recommender import MovieRecommender
import requests

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬"
)

st.title("🎬 CineMatch")
st.write("Film seç ve benzer filmleri keşfet!")

# Modeli tek sefer yükle
@st.cache_resource
def load_model():
    rec = MovieRecommender()
    rec.build_model()
    return rec

recommender = load_model()

# OMDb API
API_KEY = "1c3f99a3"

def get_movie_info(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={API_KEY}"

    response = requests.get(url)

    try:
        return response.json()
    except:
        return {}

# Tüm filmleri getir
movie_list = sorted(
    recommender.movies_df["title"].tolist()
)

# Açılır liste
movie_name = st.selectbox(
    "🎬 Film seç:",
    movie_list
)

# Kaç öneri
top_n = st.slider(
    "Kaç öneri gösterilsin?",
    min_value=1,
    max_value=10,
    value=5
)

if st.button("Önerileri Göster 🚀"):

    try:

        recommendations = recommender.get_recommendations(
            movie_name,
            top_n
        )

        st.success("Benzer filmler bulundu!")

        for _, row in recommendations.iterrows():

            movie_title = row["title"].split("(")[0].strip()

            movie = get_movie_info(movie_title)

            st.subheader(
                movie.get(
                    "Title",
                    row["title"]
                )
            )

            # Poster
            if (
                "Poster" in movie
                and movie["Poster"] != "N/A"
            ):
                st.image(
                    movie["Poster"],
                    width=200
                )

            st.write(
                "📅 Yıl:",
                movie.get(
                    "Year",
                    "Bilinmiyor"
                )
            )

            st.write(
                "⭐ IMDb:",
                movie.get(
                    "imdbRating",
                    "Bilinmiyor"
                )
            )

            st.write(
                "🎭 Tür:",
                movie.get(
                    "Genre",
                    row["genres"]
                )
            )

            st.write(
                "📝 Konu:",
                movie.get(
                    "Plot",
                    "Yok"
                )
            )

            st.write(
                f"🎯 Benzerlik: {row['similarity_score']:.2f}"
            )

            st.divider()

    except Exception as e:
        st.error(
            f"Hata oluştu: {str(e)}"
        )