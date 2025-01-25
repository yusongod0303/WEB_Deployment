import boto3
import os
from dotenv import load_dotenv
from KMeans import KeywordClusterRecommender

load_dotenv()

def download_model_files():
    s3 = boto3.client(
        )
    
    bucket_name = 'lg-lastpj-bucket'
    files = {
    }
    
    os.makedirs('./models', exist_ok=True)
    for s3_path, local_file in files.items():
        local_path = f'./models/{local_file}'
        s3.download_file(bucket_name, s3_path, local_path)

def initialize():
    try:
        download_model_files()
        return KeywordClusterRecommender.load_recommender('./models/keyword_recommender.pkl')
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    recommender = initialize()
