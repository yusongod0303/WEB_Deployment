import pymongo
import pandas as pd
import numpy as np
import re
from gensim.models import FastText

'''
홈쇼핑 데이터 가져오기
'''
# MongoDB 클라이언트 연결 (로컬 MongoDB 연결)
client = pymongo.MongoClient("mongodb+srv://yusongod:gogogo1234@lglastproject.7etr9.mongodb.net/")

# 사용할 데이터베이스 선택
db = client["homeshop"]

# 데이터베이스 내 컬렉션 선택
collection = db["drop_duplicates_Total"]

# 모든 데이터 가져오기
shop_total = collection.find()

# MongoDB 데이터를 pandas DataFrame으로 변환
shop_total = pd.DataFrame(list(shop_total))

# 'Category', 'Keyword1', 'Keyword2', 'Keyword3' 컬럼 제거
shop_total = shop_total.drop(columns=['url','image_url', 'rating', 'reviews', 'purchases','company'])
shop_total = shop_total.rename(columns={'Category': 'category'})

'''
전처리
'''
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import re
import nltk
import numpy as np

# 전처리 함수 정의
def preprocess_product_name(name):
    # 1. []와 () 사이의 단어 제거
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    # 2. 특수문자 및 특수기호 제거
    name = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', name)
    # 문자열 양끝 공백 제거
    return name.strip()

# 숫자와 영어를 제외하는 함수 정의
def remove_numbers_and_english(text):
    # 숫자와 영어 알파벳을 제외하고 한글만 남기기
    return re.sub(r'[^가-힣\s]', '', text)

# 텍스트 전처리 함수
nltk.download('stopwords')
stop_words = set(nltk.corpus.stopwords.words('english'))
def preprocess(text):
    text = re.sub(r'\W', ' ', text)  # 특수 문자 제거
    text = text.lower()  # 소문자로 변환
    text = ' '.join([word for word in text.split() if word not in stop_words])  # 불용어 제거
    return text

# 불용어 리스트 정의
stop_words = {
    '개', '종', '수', '병', '포', '팩', '장', '대', '캔', '봉', '매', '세트', '개입', '포기', '판', '구',
    '팩트', '롤', '쪽', '줄', '단', '정', '전용', '한정', '무료', '특가', '구성', '최대', '본품', '기본',
    '옵션', '증정', '패키지', '신제품', '리미티드', '클래식', '스페셜', '프리미엄', '고급', '저가', '사은품',
    '정품', '정식', '정량', '정가', '정도', '박스', '통', '팩', '총', '개월분', '종세트', '미', '벌', '특별세일전',
    '단독', '공영쇼핑', '사랑', '마리' ,'모바일앱', '할인', '공구', '년', '신상', '최신상', '모바일', '기획',
    '만원', '직', '방송중에만', '방송에서만', '파격', '각', '개씩', '일', '개월', '무료', '무료체험분', '무료체험',
    '일치', '일분', '체험', '체험분', '색상', '택', '최저가찬스', '만원인하', '방송한정가격', '이', '가격', '주분',
    '포함', '추가', '더', '박스에', '특집', '신상품', '신상'
}

# 영어, 숫자, 특수문자, 불용어를 제거하고 문자열 형태로 반환하는 함수
def custom_preprocess(text):
    # 한글만 추출하고, 영어, 숫자, 특수문자 제외
    tokens = re.findall(r'[가-힣]+', text)  # 한글만 추출
    # 불용어를 제거
    filtered_tokens = [word for word in tokens if word not in stop_words]
    # 리스트를 문자열로 합쳐서 반환
    return ' '.join(filtered_tokens)


# 문장 형식으로 변환
shop_total['문장'] = shop_total.apply(lambda row: f"{row['title']} {row['category']}", axis=1)
shop_total['문장'] = shop_total['문장'].apply(preprocess_product_name).apply(remove_numbers_and_english).apply(custom_preprocess)


'''
트렌드 데이터 가져오기
'''
# MongoDB 클라이언트 연결 (로컬 MongoDB 연결)
client = pymongo.MongoClient("mongodb+srv://yusongod:gogogo1234@lglastproject.7etr9.mongodb.net/")

# 사용할 데이터베이스 선택
db = client["Naver"]

# 데이터베이스 내 컬렉션 선택
collection = db["naver"]

# 모든 데이터 가져오기
trend_df = collection.find()

# MongoDB 데이터를 pandas DataFrame으로 변환
trend_df = pd.DataFrame(list(trend_df))

## 최근 키워드 추출

trend_df = trend_df[trend_df['period'] == '일간']
trend_df['datetime'] = trend_df['datetime'].str.extract(r'(\d{4}\.\d{2}\.\d{2})')[0]
trend_df['datetime'] = pd.to_datetime(trend_df['datetime'], format='%Y.%m.%d', errors='coerce')
trend_df = trend_df.dropna(subset=['datetime'])
# 최신 datetime 추출
latest_datetime = trend_df['datetime'].max()
# 최신 datetime과 일치하는 행 필터링
latest_trend_df = trend_df[trend_df['datetime'] == latest_datetime]
trend_key = latest_trend_df['Keyword'].drop_duplicates()
trend_key

'''
전처리
'''
# Check unique values in the 'category' column
unique_categories = shop_total['category'].unique()
print(unique_categories)

# shop_total의 price 컬럼을 숫자형으로 변환 (NaN 또는 문자열 값 처리 포함)
shop_total['price'] = pd.to_numeric(shop_total['price'], errors='coerce')  # 숫자로 변환, 변환 불가 시 NaN
shop_total['price'].fillna(0, inplace=True)  # NaN 값을 0으로 대체


'''
임베딩 모델 불러오기
'''
# 학습된 모델 로드
from gensim.models import FastText

model = FastText.load("./models/fasttext_wikipedia.model")

'''
임베딩
'''

# 문장을 FastText 임베딩으로 변환
def embed_sentence(text, model):
    # 문자열을 공백으로 분리해 단어 리스트로 변환
    words = text.split()
    # 단어 임베딩 추출
    word_vectors = [
        model.wv[word] for word in words if word in model.wv
    ]
    if word_vectors:
        return np.mean(word_vectors, axis=0)  # 단어 벡터 평균
    else:
        return np.zeros(model.vector_size)  # 빈 리스트의 경우 0 벡터 반환

# 데이터프레임에 임베딩 추가
shop_total['임베딩'] = shop_total['문장'].apply(
    lambda text: embed_sentence(text, model)
)

'''
가상 데이터
'''

## 1 데이터 준비
#상품 데이터 : shop_total
#shop_total의 컬럼 '_id' (고유 아이디), 'broadcast_time', 'title', 'price', 'datetime', 'category', 'Keyword1', 'Keyword2', 'Keyword3', '문장', '임베딩'(임베딩 값), '유사도', '클러스터'

# 사용자 데이터 (예시)
user_data = {
    'user_id': ['dydtns76'],
    'age': '20대',
    'gender': '여성',
    'preferred_category': [['패션의류', '디지털/가전', '패션잡화']],
}

user_df = pd.DataFrame(user_data)

# 가상의 이벤트 생성
event_types = ['클릭', '검색', '즐겨찾기 추가']

# 로그 데이터
log_data = [
    {'user_id': 'dydtns76', '이벤트': '즐겨찾기 추가', '이벤트 시간': '2025-01-01 23:12:11', '이벤트 내용': '677366e6d32e6f3e277cf68a'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 23:20:00', '이벤트 내용': '677366e6d32e6f3e277cdcfa'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 23:19:50', '이벤트 내용': '677366e6d32e6f3e277cdd0d'},
    {'user_id': 'dydtns76', '이벤트': '즐겨찾기 추가', '이벤트 시간': '2025-01-01 23:15:00', '이벤트 내용': '677366e6d32e6f3e277cdd12'},
    {'user_id': 'dydtns76', '이벤트': '검색', '이벤트 시간': '2025-01-01 23:14:00', '이벤트 내용': '코트'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 23:12:11', '이벤트 내용': '677366e6d32e6f3e277cf68a'}, #
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 23:10:20', '이벤트 내용': '677366e6d32e6f3e277cff72'}, #
    {'user_id': 'dydtns76', '이벤트': '검색', '이벤트 시간': '2025-01-01 23:05:00', '이벤트 내용': '여성 코트'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 20:20:00', '이벤트 내용': '677366e6d32e6f3e277cec9b'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 20:00:00', '이벤트 내용': '677366e6d32e6f3e277cec9a'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 15:10:00', '이벤트 내용': '677366e6d32e6f3e277cdd8d'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 15:00:00', '이벤트 내용': '677366e6d32e6f3e277cdd7e'},
    {'user_id': 'dydtns76', '이벤트': '검색', '이벤트 시간': '2025-01-01 23:14:00', '이벤트 내용': '목걸이'},
    {'user_id': 'dydtns76', '이벤트': '즐겨찾기 추가', '이벤트 시간': '2025-01-01 08:13:12', '이벤트 내용': '677366e6d32e6f3e277ce940'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 08:12:11', '이벤트 내용': '677366e6d32e6f3e277cf7ac'},
    {'user_id': 'dydtns76', '이벤트': '클릭', '이벤트 시간': '2025-01-01 08:10:20', '이벤트 내용': '677366e6d32e6f3e277ce946'},
    {'user_id': 'dydtns76', '이벤트': '검색', '이벤트 시간': '2025-01-01 08:00:00', '이벤트 내용': '냉장고'}
] #이벤트 내용: 클릭한 상품 아이디나 검색한 키워드 shop_total의 컬럼 '_id'와 연결 가능

log_df = pd.DataFrame(log_data)

log_df['이벤트 내용'] = log_df['이벤트 내용'].astype(str)
shop_total['_id'] = shop_total['_id'].astype(str)

# 로그 데이터와 상품 데이터 연결
merged_df = log_df.merge(shop_total, left_on='이벤트 내용', right_on='_id', how='left')

'''
모델링
'''
import pandas as pd
import numpy as np
from datetime import datetime
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial.distance import cosine
from sklearn.metrics import precision_score, recall_score, ndcg_score

class RecommendationSystem:
    def __init__(self, encoding_dim=32, dropout_rate=0.3, noise_factor=0.1):
        self.encoding_dim = encoding_dim
        self.dropout_rate = dropout_rate
        self.noise_factor = noise_factor
        self.scaler = MinMaxScaler()
        
    def create_cdae(self, input_dim, num_users):
        # Input layers
        item_input = tf.keras.layers.Input(shape=(input_dim,), name='item_input')
        user_input = tf.keras.layers.Input(shape=(1,), name='user_input')
        
        # User embedding
        user_embedding = tf.keras.layers.Embedding(
            num_users, 
            self.encoding_dim, 
            name='user_embedding'
        )(user_input)
        user_embedding = tf.keras.layers.Flatten()(user_embedding)
        
        # Add noise to input
        noise = tf.keras.layers.GaussianNoise(self.noise_factor)(item_input)
        
        # Encoder
        encoded = tf.keras.layers.Dense(self.encoding_dim*2, activation='relu')(noise)
        encoded = tf.keras.layers.Dropout(self.dropout_rate)(encoded)
        encoded = tf.keras.layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Combine user embedding with encoded items
        merged = tf.keras.layers.Concatenate()([encoded, user_embedding])
        
        # Decoder
        decoded = tf.keras.layers.Dense(self.encoding_dim*2, activation='relu')(merged)
        decoded = tf.keras.layers.Dropout(self.dropout_rate)(decoded)
        decoded = tf.keras.layers.Dense(input_dim, activation='sigmoid')(decoded)
        
        # Create model
        model = tf.keras.Model(inputs=[item_input, user_input], outputs=decoded)
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['mse'])
        
        return model

    def calculate_weights(self, shop_total, user_df, log_data, trend_key=None):
        """가중치 특성 계산 함수"""
        if isinstance(log_data, list):
            log_data = pd.DataFrame(log_data)
        
        # 이벤트 가중치 정의
        event_weights = {
            '즐겨찾기 추가': 1.0,
            '검색': 0.7,
            '클릭': 0.5
        }
        
        # 시간 기반 가중치 계산
        current_time = datetime.now()
        recent_events = log_data.sort_values('이벤트 시간', ascending=False).head(20)
        recent_events['time_diff'] = recent_events['이벤트 시간'].apply(
            lambda x: (current_time - pd.to_datetime(x)).total_seconds()
        )
        max_time_diff = recent_events['time_diff'].max()
        
        product_weights = {}
        
        # 이벤트 및 시간 기반 가중치 계산
        for _, event in recent_events.iterrows():
            time_weight = 1.0 - 0.5 * (event['time_diff'] / max_time_diff)
            event_weight = event_weights[event['이벤트']]
            final_weight = time_weight * event_weight
            
            if event['이벤트'] == '검색':
                self._process_search_event(event, shop_total, product_weights, final_weight)
            else:
                self._process_interaction_event(event, shop_total, product_weights, final_weight)
        
        # 선호 카테고리 및 트렌드 가중치 추가
        self._add_category_weights(shop_total, user_df, product_weights)
        if trend_key is not None:
            self._add_trend_weights(shop_total, trend_key, product_weights)
        
        return product_weights
    
    def _process_search_event(self, event, shop_total, product_weights, weight):
        """검색 이벤트 처리"""
        keyword = str(event['이벤트 내용']).lower()
        matching_products = shop_total[
            shop_total['title'].str.lower().str.contains(keyword, na=False)
        ]['_id'].tolist()
        
        for prod_id in matching_products:
            product_weights[prod_id] = product_weights.get(prod_id, 0) + weight
    
    def _process_interaction_event(self, event, shop_total, product_weights, weight):
        """상호작용 이벤트 처리"""
        product_id = event['이벤트 내용']
        product_weights[product_id] = product_weights.get(product_id, 0) + weight
        
        # 유사 상품 처리
        if product_id in shop_total['_id'].values:
            self._add_similar_product_weights(
                product_id, shop_total, product_weights, weight
            )
    
    def _add_similar_product_weights(self, product_id, shop_total, product_weights, weight):
        """유사 상품 가중치 추가"""
        current_embedding = shop_total[shop_total['_id'] == product_id]['임베딩'].iloc[0]
        
        if isinstance(current_embedding, str):
            current_embedding = np.fromstring(
                current_embedding.strip('[]'), sep=',', dtype=float
            )
        
        similarities = shop_total['임베딩'].apply(
            lambda x: 1 - cosine(
                current_embedding,
                np.fromstring(x.strip('[]'), sep=',', dtype=float)
                if isinstance(x, str) else x
            )
        )
        
        similar_products = shop_total.iloc[
            similarities.nlargest(6).index[1:]
        ]['_id'].tolist()
        
        for sim_prod_id in similar_products:
            product_weights[sim_prod_id] = \
                product_weights.get(sim_prod_id, 0) + weight * 0.5
    
    def _add_category_weights(self, shop_total, user_df, product_weights):
        """선호 카테고리 가중치 추가"""
        preferred_categories = user_df['preferred_category'].iloc[0]
        if isinstance(preferred_categories, list):
            if len(preferred_categories) > 0 and isinstance(preferred_categories[0], list):
                preferred_categories = preferred_categories[0]
        
        category_products = shop_total[
            shop_total['category'].isin(preferred_categories)
        ]['_id'].tolist()
        
        for prod_id in category_products:
            product_weights[prod_id] = product_weights.get(prod_id, 0) + 1.0 # 선호 카테고리 가중치 설정
    
    def _add_trend_weights(self, shop_total, trend_key, product_weights):
        """트렌드 키워드 가중치 추가"""
        if isinstance(trend_key, (list, pd.Series)):
            for keyword in trend_key:
                trend_products = shop_total[
                    shop_total['title'].str.lower().str.contains(
                        keyword.lower(), na=False
                    )
                ]['_id'].tolist()
                
                for prod_id in trend_products:
                    product_weights[prod_id] = product_weights.get(prod_id, 0) + 0.5 # 트렌드 가중치 설정

    def train_and_recommend(self, shop_total, user_df, log_data, trend_key=None, 
                          epochs=100, batch_size=32):
        """모델 학습 및 추천 생성"""
        # 가중치 계산
        product_weights = self.calculate_weights(shop_total, user_df, log_data, trend_key)
        
        # 가중치 벡터 생성 및 정규화
        weight_vector = np.zeros(len(shop_total))
        for i, prod_id in enumerate(shop_total['_id']):
            weight_vector[i] = product_weights.get(prod_id, 0)
        
        weight_vector = self.scaler.fit_transform(
            weight_vector.reshape(-1, 1)
        ).flatten()
        
        # CDAE 모델 생성 및 학습
        user_id = user_df.index[0]  # 현재 사용자 ID
        model = self.create_cdae(len(shop_total), len(user_df))
        
        history = model.fit(
            [weight_vector.reshape(1, -1), np.array([user_id])],
            weight_vector.reshape(1, -1),
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )
        
        # 추천 생성
        predictions = model.predict(
            [weight_vector.reshape(1, -1), np.array([user_id])]
        ).flatten()
        
        # 상위 추천 항목 선택
        recommendation_indices = np.argsort(predictions)[::-1][:10]
        recommendation_scores = predictions[recommendation_indices]
        
        # 결과 생성
        recommended_products = shop_total.iloc[recommendation_indices].copy()
        recommended_products['recommendation_score'] = recommendation_scores
        
        # 평가 메트릭 계산
        metrics = self.calculate_metrics(weight_vector, predictions)
        
        return recommended_products, metrics, history
    
    def calculate_metrics(self, true_values, predictions, k=10):
        """추천 시스템 성능 평가 메트릭 계산"""
        # 이진화를 위한 임계값 설정
        threshold = np.percentile(true_values, 90)
        binary_true = (true_values > threshold).astype(int)
        binary_pred = (predictions > threshold).astype(int)
        
        # 상위 k개 항목에 대한 NDCG 계산
        ndcg = ndcg_score(
            true_values.reshape(1, -1),
            predictions.reshape(1, -1),
            k=k
        )
        
        return {
            'precision': precision_score(binary_true, binary_pred),
            'recall': recall_score(binary_true, binary_pred),
            'ndcg@k': ndcg
        }

def print_recommendations(recommended_products, metrics=None):
    """추천 결과 및 성능 메트릭 출력"""
    print("추천된 상품 목록:")
    for idx, row in recommended_products.iterrows():
        print(f"상품 ID: {row['_id']}")
        print(f"제목: {row['title']}")
        print(f"카테고리: {row['category']}")
        print(f"가격: {row['price']:.2f}")
        print(f"추천 점수: {row['recommendation_score']:.4f}")
        print("-" * 50)
    
    if metrics:
        print("\n성능 메트릭:")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall: {metrics['recall']:.4f}")
        print(f"NDCG@10: {metrics['ndcg@k']:.4f}")


# 시스템 초기화
recommender = RecommendationSystem(
    encoding_dim=32,
    dropout_rate=0.3,
    noise_factor=0.1
)

# 추천 생성
recommended_products, metrics, history = recommender.train_and_recommend(
    shop_total,
    user_df,
    log_data,
    trend_key
)