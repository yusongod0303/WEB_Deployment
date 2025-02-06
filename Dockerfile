# Python 3.9-slim 이미지를 베이스로 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    git wget unzip bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Python 라이브러리 설치
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    jinja2 \
    python-dotenv \
    pymongo \
    motor \
    pandas \
    numpy \
    scikit-learn \
    tensorflow \
    gensim \
    joblib \
    scipy \
    requests \
    passlib \
    nltk \
    bs4 \
    boto3 \
    python-multipart

# nltk 데이터 다운로드
RUN python -m nltk.downloader stopwords

# 애플리케이션 코드 복사
COPY . .

# model_loader.py 실행하여 모델 다운로드
RUN python model_loader.py

# 실행 포트 설정
EXPOSE 7777

# FastAPI 애플리케이션 실행
CMD ["uvicorn", "test:app", "--host", "0.0.0.0", "--port", "7777"]