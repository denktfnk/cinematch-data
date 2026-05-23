import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import load_data

class MovieRecommender:
    def __init__(self):
        self.movies_df = None
        self.tfidf_matrix = None
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.indices = None

    def prepare_data(self):
        """
        Loads data and prepares the 'metadata' column for TF-IDF.
        """
        print("Preparing data for recommendation model...")
        movies, tags = load_data()

        # Process genres: replace '|' with spaces
        movies['genres'] = movies['genres'].str.replace('|', ' ')

        # Process tags: group by movieId and combine tags
        tags['tag'] = tags['tag'].fillna('')
        grouped_tags = tags.groupby('movieId')['tag'].apply(lambda x: ' '.join(x)).reset_index()

        # Merge tags into movies
        self.movies_df = pd.merge(movies, grouped_tags, on='movieId', how='left')
        self.movies_df['tag'] = self.movies_df['tag'].fillna('')

        # Create metadata column combining title, genres, and tags
        self.movies_df['metadata'] = self.movies_df['title'] + " " + self.movies_df['genres'] + " " + self.movies_df['tag']

        # Create a reverse mapping of movie titles and DataFrame indices
        # Removing duplicates just in case, keeping the first occurrence
        self.indices = pd.Series(self.movies_df.index, index=self.movies_df['title']).drop_duplicates()

    def build_model(self):
        """
        Builds the TF-IDF matrix.
        """
        if self.movies_df is None:
            self.prepare_data()
        
        print("Building TF-IDF matrix...")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.movies_df['metadata'])
        print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")

    def get_recommendations(self, title, top_n=5):
        """
        Returns top N recommendations for a given movie title based on Cosine Similarity.
        """
        if self.tfidf_matrix is None:
            self.build_model()

        if title not in self.indices:
            raise ValueError(f"Movie '{title}' not found in the dataset.")

        # Get the index of the movie that matches the title
        idx = self.indices[title]

        # In case there are multiple movies with the same title, take the first one
        if isinstance(idx, pd.Series):
            idx = idx.iloc[0]

        # Compute the cosine similarity of the given movie with all movies
        # We calculate it on the fly for the specific movie to save memory
        movie_vector = self.tfidf_matrix[idx]
        sim_scores = cosine_similarity(movie_vector, self.tfidf_matrix).flatten()

        # Get the scores of all movies with their corresponding indices
        sim_scores_with_idx = list(enumerate(sim_scores))

        # Sort the movies based on the similarity scores in descending order
        sim_scores_with_idx = sorted(sim_scores_with_idx, key=lambda x: x[1], reverse=True)

        # Get the scores of the top N most similar movies (excluding the movie itself)
        # We start from 1 because the 0th item is the movie itself (similarity = 1.0)
        sim_scores_with_idx = sim_scores_with_idx[1:top_n+1]

        # Get the movie indices
        movie_indices = [i[0] for i in sim_scores_with_idx]
        scores = [i[1] for i in sim_scores_with_idx]

        # Return the top N most similar movies
        result_df = self.movies_df.iloc[movie_indices][['title', 'genres']].copy()
        result_df['similarity_score'] = scores
        return result_df

    def find_movie_title(self, query):
        """
        Finds movies matching the query (case-insensitive partial match).
        """
        if self.movies_df is None:
            self.prepare_data()
            
        matches = self.movies_df[self.movies_df['title'].str.contains(query, case=False, na=False)]
        return matches['title'].tolist()

    def evaluate_recommendations(self, target_title, recommendations_df):
        """
        Evaluates recommendations using Genre Overlap.
        Returns the average percentage of overlapping genres.
        """
        if target_title not in self.indices:
            return 0.0

        idx = self.indices[target_title]
        if isinstance(idx, pd.Series):
            idx = idx.iloc[0]

        target_genres = set(self.movies_df.loc[idx, 'genres'].split())
        
        if not target_genres or len(target_genres) == 0:
            return 0.0

        total_overlap_percentage = 0.0
        
        for _, row in recommendations_df.iterrows():
            rec_genres = set(row['genres'].split())
            overlap = target_genres.intersection(rec_genres)
            # Yüzdelik örtüşme: (kesişen tür sayısı) / (hedef filmin tür sayısı)
            overlap_percentage = len(overlap) / len(target_genres)
            total_overlap_percentage += overlap_percentage
            
        avg_overlap = total_overlap_percentage / len(recommendations_df) if len(recommendations_df) > 0 else 0.0
        return avg_overlap * 100 # Yüzde olarak döndür

if __name__ == "__main__":
    recommender = MovieRecommender()
    try:
        recommendations = recommender.get_recommendations("Toy Story (1995)", top_n=5)
        print("\nRecommendations for 'Toy Story (1995)':")
        print(recommendations)
    except Exception as e:
        print(f"Error: {e}")
