import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import pymongo
import pandas as pd
from gensim.models import FastText


class KeywordClusterRecommender:
    def __init__(self, embeddings, cluster_labels, df):
        """
        키워드 기반 클러스터 추천 시스템 초기화.
        :param embeddings: 각 데이터의 임베딩 벡터
        :param cluster_labels: 각 데이터의 클러스터 레이블
        :param df: 전체 데이터프레임
        """
        self.embeddings = embeddings
        self.cluster_labels = cluster_labels
        self.df = df
        self.titles = df['title'].fillna("").tolist()
        self.texts = df.apply(
            lambda x: ' '.join(
                str(x[col]) for col in ['Category', 'Keyword1', 'Keyword2', 'Keyword3'] if x[col] is not None),
            axis=1
        ).tolist()

    def find_index_by_keyword(self, keyword):
        """
        키워드를 포함하는 상품의 인덱스 반환
        """
        indices = [
            idx for idx, text in enumerate(self.texts)
            if keyword in text
        ]
        return indices

    def find_index_by_title(self, keyword):
        """
        제목에서 키워드를 포함하는 상품의 인덱스 반환
        """
        indices = [
            idx for idx, title in enumerate(self.titles)
            if keyword in title
        ]
        return indices

    def recommend_within_cluster_by_keyword(self, keyword, top_n=5):
        """
        키워드 기반으로 클러스터 내 유사 상품 추천.
        각 클러스터당 하나의 대표 상품만 선택하여 추천.
        """
        # 키워드로 인덱스 검색
        target_indices = self.find_index_by_keyword(keyword)

        # 키워드가 포함된 상품이 없을 경우, 제목에서 키워드를 포함하는 상품 찾기
        if not target_indices:
            print(f"키워드 '{keyword}'를 포함하는 상품이 없습니다. 제목에서 검색을 진행합니다.")
            target_indices = self.find_index_by_title(keyword)

            # 제목에서도 키워드가 포함된 상품이 없을 경우
            if not target_indices:
                print(f"제목에 '{keyword}'가 포함된 상품도 없습니다. 유사도 기반 추천을 진행합니다.")
                target_embedding = self.embeddings.mean(axis=0)
                similarities = cosine_similarity(
                    [target_embedding], self.embeddings
                )[0]
                similarity_pairs = sorted(
                    [(idx, sim) for idx, sim in enumerate(similarities)],
                    key=lambda x: x[1],
                    reverse=True
                )[:top_n]

                recommendations = [{
                    "title": self.df.iloc[idx]['title'],
                    "price": self.df.iloc[idx]['price'],
                    "image_url": self.df.iloc[idx]['image_url'],
                    "url": self.df.iloc[idx]['url'],
                    "similarity": sim
                } for idx, sim in similarity_pairs]

                print("\n유사도 기반 추천 상품:")
                for r in recommendations:
                    print(f"제목: {r['title']}")
                    print(f"가격: {r['price']}")
                    print(f"이미지: {r['image_url']}")
                    print(f"링크: {r['url']}")
                    print(f"유사도: {r['similarity']:.4f}\n")
                return recommendations

        # 클러스터별로 가장 연관성 높은 상품 하나씩만 선택
        cluster_representatives = {}
        for idx in target_indices:
            if idx >= len(self.cluster_labels):  # idx가 클러스터 레이블의 범위를 벗어나면 건너뛰기
                continue
            cluster = self.cluster_labels[idx]
            if cluster not in cluster_representatives or \
                    keyword in self.titles[idx]:  # 제목에 키워드가 있는 상품 우선 선택
                cluster_representatives[cluster] = idx

        # 선택된 대표 상품들에 대해서만 추천 진행
        recommendations = []
        print(f"\n키워드 '{keyword}'로 검색된 대표 상품들:")
        for cluster, target_idx in cluster_representatives.items():
            if target_idx >= len(self.embeddings):  # embeddings의 범위도 확인
                continue
            target_embedding = self.embeddings[target_idx]

            # 동일 클러스터의 데이터 필터링
            cluster_indices = [
                idx for idx, label in enumerate(self.cluster_labels)
                if label == cluster
            ]
            cluster_embeddings = self.embeddings[cluster_indices]

            # 코사인 유사도 계산
            similarities = cosine_similarity(
                [target_embedding], cluster_embeddings
            )[0]

            # 대상 상품 제외 및 유사도 정렬
            similarity_pairs = [
                (cluster_indices[idx], sim) for idx, sim in enumerate(similarities)
                if cluster_indices[idx] != target_idx
            ]
            similarity_pairs.sort(key=lambda x: x[1], reverse=True)

            # 추천 상품 리스트 생성
            seen_titles = set()
            filtered_pairs = []
            for idx, sim in similarity_pairs:
                if self.titles[idx] not in seen_titles:
                    seen_titles.add(self.titles[idx])
                    filtered_pairs.append({
                        "title": self.df.iloc[idx]['title'],
                        "price": self.df.iloc[idx]['price'],
                        "image_url": self.df.iloc[idx]['image_url'],
                        "url": self.df.iloc[idx]['url'],
                        "similarity": sim
                    })
                if len(filtered_pairs) == top_n:
                    break

            target_product = {
                "title": self.df.iloc[target_idx]['title'],
                "price": self.df.iloc[target_idx]['price'],
                "image_url": self.df.iloc[target_idx]['image_url'],
                "url": self.df.iloc[target_idx]['url']
            }

            recommendations.append({
                "target_product": target_product,
                "cluster": cluster,
                "recommendations": filtered_pairs
            })

        # 결과 출력
        for rec in recommendations:
            print(f"\n대표 상품 (클러스터 {rec['cluster']}):")
            print(f"title: {rec['target_product']['title']}")
            print(f"price: {rec['target_product']['price']}")
            print(f"image_url: {rec['target_product']['image_url']}")
            print(f"url: {rec['target_product']['url']}")

            print("\n추천 상품들:")
            for r in rec['recommendations']:
                print(f"\ntitle: {r['title']}")
                print(f"price: {r['price']}")
                print(f"image_url: {r['image_url']}")
                print(f"url: {r['url']}")

        return recommendations

    @classmethod
    def load_models(cls, data_path=None):
        """
        저장된 모델들을 로드하여 추천 시스템 초기화
        """
        # MongoDB에서 데이터 로드
        if data_path is None:
            client = pymongo.MongoClient("mongodb+srv://yusongod:gogogo1234@lglastproject.7etr9.mongodb.net/")
            db = client["homeshop"]
            collection = db["drop_duplicates_Total"]
            df = pd.DataFrame(list(collection.find()))

            # 데이터 전처리
            df['price'] = df['price'].replace('NaN', np.nan)
            df['price'] = df['price'].apply(lambda x: x.replace(',', '') if isinstance(x, str) and ',' in x else x)
            df = df[df['Category'] != 'Unknown']
            df = df.dropna(subset='price', ignore_index=True)

        else:
            df = pd.read_csv(data_path)

        # 모델 및 클러스터 레이블 로드
        fasttext_model = FastText.load('fasttext_model.model')
        cluster_labels = np.load('cluster_labels_optimal.npy')

        # 임베딩 계산
        texts = df.apply(
            lambda x: ' '.join(
                str(x[col]) for col in ['Category', 'Keyword1', 'Keyword2', 'Keyword3'] if x[col] is not None),
            axis=1
        ).tolist()

        embeddings = np.array([
            np.mean([fasttext_model.wv[word] for word in text.split() if word in fasttext_model.wv]
                    or [np.zeros(fasttext_model.vector_size)], axis=0)
            for text in texts
        ])

        return cls(embeddings, cluster_labels, df)


    @classmethod
    def load_recommender(cls, path):
        """
        저장된 추천 시스템 로드
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return cls(**data)


if __name__ == "__main__":
    loaded_recommender = KeywordClusterRecommender.load_recommender('./models/keyword_recommender.pkl')
    recommendations = loaded_recommender.recommend_within_cluster_by_keyword(keyword, top_n=10)