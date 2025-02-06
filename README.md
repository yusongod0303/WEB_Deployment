# 홈쇼핑 데이터 기반 추천 시스템 🚀

## 프로젝트 개요 📄
이 프로젝트는 홈쇼핑 데이터를 기반으로 사용자의 검색 및 클릭 데이터를 분석하여 유사한 상품을 추천하는 시스템입니다. FastAPI 기반 웹 애플리케이션과 머신러닝 모델을 통합하여 실시간 추천 기능을 제공합니다.

---

## 주요 기능 🌟
- **유저별 맞춤형 추천**: 사용자가 최근 검색하거나 클릭한 상품과 유사한 제품 추천.
- **트렌드 기반 추천**: 네이버 트렌드 데이터를 반영하여 인기 있는 키워드와 관련된 상품 추천.
- **클러스터 기반 추천**: KMeans 군집화 알고리즘을 이용해 클러스터 내 유사 상품 추천.
- **자동화 배포**: Docker를 이용하여 손쉬운 배포 및 실행 가능.

---

## 디렉토리 구조 📂
 
WEB_DEPLOYMENT
├── CDAE.py # CDAE 기반 추천 시스템  
├── Dockerfile # Docker 설정 파일  
├── KMeans.py # KMeans 기반 추천 시스템  
├── model_loader.py # Amazon S3에서 모델 다운로드  
├── test.py # FastAPI 서버 및 메인 로직  
├── templates/ # HTML 템플릿 폴더 (디자인 관련)  
│ ├── detail.html  
│ ├── edit.html  
│ ├── favorite.html  
│ ├── login.html  
│ ├── main.html  
│ ├── myinfo.html  
│ ├── schedule.html  
│ ├── search.html  
│ ├── signup.html  
│ └── trend.html  
└── templates/static/img/ # 정적 이미지 디렉토리  
├── 003.png  
└── 006.png  

---

## Dockerfile을 이용한 배포 🛠️

1. Docker 이미지 빌드  
`docker build -t homeshop-recommender .`

2. Docker 컨테이너 실행  
`docker run -p 7777:7777 homeshop-recommender`

---

## 주요 코드 설명 📄

### 1. test.py (FastAPI 애플리케이션)
* 로그인 및 회원가입: 사용자 인증 및 세션 관리
* 상품 추천 API: 사용자가 검색한 키워드와 최근 클릭 로그를 바탕으로 상품 추천 
* MongoDB와의 연결: 사용자 정보, 추천 로그, 홈쇼핑 데이터 등을 비동기로 관리

### 2. model_loader.py (S3에서 모델 다운로드)
* Amazon S3 연결: S3 버킷에서 모델을 다운로드하고 현재 디렉토리에 저장
* 자동 모델 로드: 애플리케이션 시작 전에 최신 모델을 불러옴

### 3. KMeans.py (KMeans 기반 추천 시스템)
* 상품 군집화: KMeans 알고리즘으로 상품을 클러스터링하여 유사한 상품을 묶음
* 유사도 기반 추천: 클러스터 내에서 코사인 유사도를 기반으로 상위 추천 상품 제공

### 4. CDAE.py (Collaborative Denoising Autoencoder 기반 추천)
* 사용자 행동 가중치 반영: 최근 클릭, 검색, 즐겨찾기 이벤트에 따라 상품 가중치를 계산
* 딥러닝 기반 추천: CDAE 모델을 학습하여 사용자 맞춤형 추천 제공