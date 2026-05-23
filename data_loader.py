import os
import requests
import zipfile
import pandas as pd

DATA_DIR = "data"
DATASET_URL = "https://files.grouplens.org/datasets/movielens/cinematch_dataset.zip"
ZIP_PATH = os.path.join(DATA_DIR, "cinematch_dataset.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "cinematch_dataset")

def download_and_extract():
    """
    Downloads the MovieLens Latest Small dataset if it doesn't exist and extracts it.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(ZIP_PATH) and not os.path.exists(EXTRACT_DIR):
        print(f"Downloading dataset from {DATASET_URL}...")
        response = requests.get(DATASET_URL, stream=True)
        response.raise_for_status()
        
        with open(ZIP_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")

    if not os.path.exists(EXTRACT_DIR):
        print("Extracting dataset...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        print("Extraction complete.")
    else:
        print("Dataset already exists.")

def load_data():
    """
    Loads movies and tags dataframes.
    Returns:
        movies_df (pd.DataFrame): Movies data
        tags_df (pd.DataFrame): Tags data
    """
    download_and_extract()
    
    movies_path = os.path.join(EXTRACT_DIR, "movies.csv")
    tags_path = os.path.join(EXTRACT_DIR, "tags.csv")
    
    print("Loading data into Pandas DataFrames...")
    movies_df = pd.read_csv(movies_path)
    tags_df = pd.read_csv(tags_path)
    
    return movies_df, tags_df

if __name__ == "__main__":
    movies, tags = load_data()
    print(f"Loaded {len(movies)} movies and {len(tags)} tags.")
