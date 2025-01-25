import urllib.request
import json
import pandas as pd
from fastapi import FastAPI, Form, Request, HTTPException, Query, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from passlib.context import CryptContext  # 비밀번호 해싱을 위해
import requests
from collections import defaultdict
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
import KMeans
from CDAE import recommended_products

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# 정적 파일 설정: "/static" 경로를 "templates/static" 디렉토리에 매핑
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# 비밀번호 해싱을 위한 패스워드 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = AsyncIOMotorClient('mongodb+srv://yusongod:gogogo1234@lglastproject.7etr9.mongodb.net/')  # MongoDB 로컬 주소 또는 Atlas 연결 URI

naver_db = client.Naver  # 네이버 데이터베이스
trends_collection = naver_db.naver  # 트렌드 컬렉션

shop_db = client.homeshop  # 쇼핑 데이터베이스
total_data_collection = shop_db.Total  # 상품 컬렉션
duplicate_data_collection = shop_db.drop_duplicates_Total  # 중복 데이터 컬렉션
filter_data_collection = shop_db.date_filter

users_db = client.Users_db  # 사용자 데이터베이스
users_collection = users_db.users  # 사용자 컬렉션
favorite_collection = users_db.favorite

# 간단한 로그인 상태 추적을 위한 변수
logged_in_user = None

# 카테고리 목록
categories_list = [
    "패션의류", "패션잡화", "화장품/미용", "디지털/가전", "가구/인테리어",
    "출산/육아", "식품", "스포츠/레저", "생활/건강", "여가/생활편의"
]
# 사용자 정보 모델
class User(BaseModel):
    username: str
    password: str

# 방송 상품 모델
class BroadcastItem(BaseModel):
    broadcast_time: str
    title: str
    url: str
    image_url: str
    price: int

@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    global logged_in_user
    if logged_in_user:
        # MongoDB에서 최근 시청한 데이터 가져오기
        recent_watch = await log_collection.find().to_list(None)

        # CDAE.py에서 추천 상품 데이터프레임 불러오기
        products = []
        for idx, row in recommended_products.iterrows():
            title = row['title']
            total_data = await duplicate_data_collection.find_one({"title": title})
            
            if total_data:
                product_info = {
                    "id": row['_id'],
                    "title": title,
                    "category": row['category'],
                    "price": int(row['price']),  # price를 int로 변환
                    "recommendation_score": f"{row['recommendation_score']:.4f}",
                    "url": total_data.get("url", "No URL"),
                    "image_url": total_data.get("image_url", "No Image URL"),
                }
                products.append(product_info)

        # HTML 템플릿 렌더링
        return templates.TemplateResponse("main.html", {
            "request": request,
            "recent_watch": recent_watch,
            "logged_in_user": logged_in_user,
            "products": products
        })
    else:
        return templates.TemplateResponse("main.html", {
            "request": request,
            "logged_in_user": logged_in_user
            })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error_message": None, "logged_in_user": logged_in_user})

# 로그인 처리 엔드포인트
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    global logged_in_user
    user = await users_collection.find_one({"username": username})
    
    if user and pwd_context.verify(password, user["password"]):
        logged_in_user = username
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error_message": "Invalid credentials. Please try again."
        })
    
# 닉네임 중복 확인
@app.post("/check_nickname")
async def check_nickname(nickname: str = Form(...)):
    # 아이디가 이미 존재하는지 확인
    existing_user = await users_collection.find_one({"nickname": nickname})
    if existing_user:
        return {"message": "Username already exists", "status": "error"}
    return {"message": "Username is available", "status": "success"}

# 아이디 중복 확인
@app.post("/check_username")
async def check_username(username: str = Form(...)):
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        return {"message": "Username already exists", "status": "error"}
    return {"message": "Username is available", "status": "success"}

# 이메일 중복 확인
@app.post("/check_email")
async def check_email(email: str = Form(...)):
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        return {"message": "Email already exists", "status": "error"}
    return {"message": "Email is available", "status": "success"}

# 회원가입 페이지 (선호 카테고리 포함)
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "categories": categories_list})

@app.post("/signup")
async def signup(
    request: Request,
    nickname: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    birthday: str = Form(...),
    gender: str = Form(...),
    selected_categories: list = Form(...),
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = pwd_context.hash(password)

    existing_nick = await users_collection.find_one({"nickname": nickname})
    if existing_nick:
        raise HTTPException(status_code=400, detail="Nickname already exists")
    
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    existing_email = await users_collection.find_one({"email": email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user_data = {
        "nickname": nickname,
        "username": username,
        "name": name,
        "phone": phone,
        "email": email,
        "password": hashed_password,
        "birthday": birthday,
        "gender": gender,
        "preferences": selected_categories,
    }
    try:
        result = await users_collection.insert_one(user_data)
        if result.inserted_id:
            return RedirectResponse(url="/login", status_code=303)
        else:
            raise HTTPException(status_code=500, detail="Failed to insert user data into the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/logout")
async def logout():
    global logged_in_user
    logged_in_user = None
    return RedirectResponse(url="/")

# 네이버 트렌드 API를 호출하여 데이터 가져오는 함수
def get_trend_data_from_naver(keyword: str):
    client_id = "qhL8OhsN455IeP1qEv6n"  # 네이버 API Client ID
    client_secret = "6JUDzoXBpI"  # 네이버 API Client Secret
    url = "https://openapi.naver.com/v1/datalab/search"
    body = f"""
    {{
        "startDate": "2024-12-01",
        "endDate": "2025-01-22",
        "timeUnit": "date",
        "keywordGroups": [
            {{
                "groupName": "{keyword}",
                "keywords": ["{keyword}"]
            }}
        ],
        "device": "pc",
        "ages": ["2", "3"],
        "gender": "f"
    }}
    """
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")
    response = urllib.request.urlopen(request, data=body.encode("utf-8"))
    rescode = response.getcode()

    if rescode == 200:
        response_body = response.read().decode("utf-8")
        data = json.loads(response_body)
        result_list = []
        for keyword_group in data["results"]:
            group_name = keyword_group["title"]
            for item in keyword_group["data"]:
                result_list.append({
                    "date": item["period"],
                    "ratio": item["ratio"]
                })
        
        return result_list
    else:
        return None
    
@app.get("/products-by-price-range")
async def products_by_price_range(price_range: str = Query(...)):
    # 가격 필터링 조건 설정
    price_filter_conditions = {}

    # 가격 범위에 따라 필터링
    if price_range == "under_10000":
        price_filter_conditions["price"] = {"$lt": 10000}
    elif price_range == "10000_30000":
        price_filter_conditions["price"] = {"$gte": 10000, "$lt": 30000}
    elif price_range == "30000_50000":
        price_filter_conditions["price"] = {"$gte": 30000, "$lt": 50000}
    elif price_range == "50000_100000":
        price_filter_conditions["price"] = {"$gte": 50000, "$lt": 100000}
    elif price_range == "above_100000":
        price_filter_conditions["price"] = {"$gte": 100000}
    elif price_range == "100000_200000":
        price_filter_conditions["price"] = {"$gte": 100000, "$lt": 200000}
    elif price_range == "above_200000":
        price_filter_conditions["price"] = {"$gte": 200000}

    # 가격 범위에 맞는 상품 데이터를 가져오기
    filtered_products = await duplicate_data_collection.find(price_filter_conditions).to_list(length=None)

    for product in filtered_products:
        try:
            product['price'] = int(product['price'])
        except ValueError:
            product['price'] = 0

    # 가격을 기준으로 오름차순 정렬
    filtered_products = sorted(filtered_products, key=lambda x: x.get('price', 0))

    # 결과 반환
    return filtered_products

# 트렌드 페이지 - 카테고리 선택 후 필터링된 트렌드만 표시
@app.get("/trend", response_class=HTMLResponse)
async def show_trends(request: Request, category: str = Query(None), price_range: str = Query(None), keyword: str = Query(None)):
    # period가 '일간'인 데이터만 가져오기
    cursor = trends_collection.aggregate([
        {"$match": {"period": "일간"}},  # period가 '일간'인 데이터만 필터링
        {"$group": {"_id": "$datetime"}}  # datetime 값으로 그룹화하여 고유한 datetime만 가져옴
    ])
    unique_datetimes = [doc["_id"] for doc in await cursor.to_list(length=None)]
    
    # 고유한 categories 값(카테고리)만 가져오기 (period가 '일간'인 데이터만)
    cursor = trends_collection.aggregate([
        {"$match": {"period": "일간"}},  # period가 '일간'인 데이터만 필터링
        {"$group": {"_id": "$categories"}}  # categories 값으로 그룹화하여 고유한 categories만 가져옴
    ])
    unique_categories = [doc["_id"] for doc in await cursor.to_list(length=None)]

    # 고유 datetime과 categories들을 정렬
    unique_datetimes.sort()
    unique_categories.sort()

    # 기본적으로 가장 최근 datetime과 카테고리를 선택하도록 설정
    datetime = unique_datetimes[-1]  # 가장 최근 datetime 선택

    if not category and unique_categories:
        category = unique_categories[-1]  # 가장 최근 category 선택

    # 필터링 조건 설정
    filter_conditions = {
        "period": "일간",  # period가 '일간'인 데이터만 필터링
        "datetime": datetime  # 가장 최근 datetime 필터링
    }

    if category:
        filter_conditions['categories'] = category

    # 필터링된 트렌드 데이터 가져오기
    filtered_trends = await trends_collection.find(filter_conditions).to_list(length=None)

    # 가격 필터링 조건 설정
    price_filter_conditions = {}
    if price_range:
        if price_range == "under_10000":
            price_filter_conditions["price"] = {"$lt": 10000}
        elif price_range == "10000_30000":
            price_filter_conditions["price"] = {"$gte": 10000, "$lt": 30000}
        elif price_range == "30000_50000":
            price_filter_conditions["price"] = {"$gte": 30000, "$lt": 50000}
        elif price_range == "50000_100000":
            price_filter_conditions["price"] = {"$gte": 50000, "$lt": 100000}
        elif price_range == "above_100000":
            price_filter_conditions["price"] = {"$gte": 100000}
        elif price_range == "100000_200000":
            price_filter_conditions["price"] = {"$gte": 100000, "$lt": 200000}
        elif price_range == "above_200000": 
            price_filter_conditions["price"] = {"$gte": 200000}
    
    # 가격 범위에 맞는 상품 데이터 가져오기
    filtered_products = await duplicate_data_collection.find(price_filter_conditions).to_list(length=None)

    for product in filtered_products:
        try:
            product['price'] = int(product['price'])
        except ValueError:
            product['price'] = 0

    # 가격 오름차순 정렬
    filtered_products = sorted(filtered_products, key=lambda x: x.get('price', 0))

    # 키워드 필터링
    if keyword:
        filtered_products = [product for product in filtered_products if any(keyword in product.get(f"Keyword{i}", "") for i in range(1, 4))]

    # 상품 제목과 URL을 함께 추출
    product_links = [{"title": product["title"], "url": product["url"], "price": product["price"], "image_url": product["image_url"]} for product in filtered_products]


    return templates.TemplateResponse("trend.html", {
        "request": request,
        "unique_categories": unique_categories,  # 고유 categories 목록 (정렬된 상태)
        "filtered_trends": filtered_trends,
        "datetime": datetime,  # 가장 최근 datetime 값 전달
        "logged_in_user": logged_in_user,  # 로그인된 사용자 정보
        "filtered_products": filtered_products,  # 가격 범위에 맞는 상품들 (정렬됨)
        "selected_price_range": price_range,  # 선택된 가격 범위
        "product_links": product_links,
    })

# 트렌드 데이터 (Ajax용)
@app.get("/trend-data")
async def trend_data(keyword: str):
    trend_data = get_trend_data_from_naver(keyword)
    
    if trend_data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch trend data from Naver")

    return trend_data

@app.get("/schedule", response_class=HTMLResponse)
async def read_schedule(request: Request, company: str = '', date: str = ''):
    cursor = filter_data_collection.find()
    broadcast_data = defaultdict(lambda: defaultdict(list))
    company_dates = defaultdict(set)
    
    # 데이터 로깅 추가
    print("Starting to fetch data from MongoDB")
    
    async for document in cursor:
        title = document['title']
        broadcast_time = document['broadcast_time']
        datetime_str = document['datetime']
        company_name = document['company']
        url = document.get('url', '')
        image_url = document.get('image_url', '')
        price = document.get('price', 0)
        
        # 데이터 로깅
        print(f"Processing document: {company_name} - {datetime_str}")

        date = datetime_str if isinstance(datetime_str, str) else str(datetime_str)
        
        # 필터링 조건 수정
        if company and company_name != company:
            continue

        if date and date != datetime_str:
            continue

        broadcast_data[company_name][datetime_str].append({
            "title": title,
            "broadcast_time": broadcast_time,
            "url": url,
            "image_url": image_url,
            "price": price
        })
        
        company_dates[company_name].add(date)
    
    # 정렬된 회사와 날짜 목록
    sorted_company_dates = sorted(company_dates.keys())
    all_dates = sorted(set(date for dates in company_dates.values() for date in dates))
    
    # 데이터 로깅
    print(f"Found {len(sorted_company_dates)} companies and {len(all_dates)} dates")
    print(f"Broadcast data: {dict(broadcast_data)}")

    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "broadcast_data": broadcast_data,
        "sorted_company_dates": sorted_company_dates,
        "all_dates": all_dates,
        "selected_company": company,
        "selected_date": date,
        "logged_in_user": logged_in_user
    })

# 즐겨찾기 추가/제거 API
@app.post("/toggle_favorite")
async def toggle_favorite(item: BroadcastItem):
    global logged_in_user
    if not logged_in_user:
        raise HTTPException(status_code=401, detail="User not logged in")

    # 사용자 정보 확인
    user = await users_collection.find_one({"username": logged_in_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 즐겨찾기 데이터 구조
    favorite_item = {
        "broadcast_time": item.broadcast_time,
        "title": item.title,
        "url": item.url,
        "image_url": item.image_url,
        "price": item.price
    }

    # 즐겨찾기 추가/제거 처리
    existing_favorite = await favorite_collection.find_one({
        "username": logged_in_user,
        "title": item.title
    })

    if existing_favorite:
        # 이미 즐겨찾기 되어 있으면 삭제
        await favorite_collection.delete_one({"_id": existing_favorite["_id"]})
        return {"message": "즐겨찾기 제거"}
    else:
        # 즐겨찾기 추가
        await favorite_collection.insert_one({
            "username": logged_in_user,
            "broadcast_time": item.broadcast_time,
            "title": item.title,
            "url": item.url,
            "image_url": item.image_url,
            "price": item.price
        })
        return {"message": "즐겨찾기 추가"}

# 즐겨찾기 목록 가져오기
@app.get("/favorites")
async def favorites(request: Request):
    if logged_in_user:
        # 즐겨찾기 목록 가져오기
        favorites = await favorite_collection.find({"username": logged_in_user}).to_list(None)
        return templates.TemplateResponse("favorite.html", {"request": request, "favorites": favorites, "logged_in_user": logged_in_user})
    else:
        return templates.TemplateResponse("login.html", {"request": request})

@app.post("/remove_favorite/{favorite_id}")
async def remove_favorite(favorite_id: str):
    result = await favorite_collection.delete_one({"_id": favorite_id})
    if result.deleted_count > 0:
        return {"message": "즐겨찾기 제거"}
    else:
        return {"message": "Error removing favorite"}

# 마이페이지 페이지 (비밀번호 입력 폼 포함)
@app.get("/myinfo", response_class=HTMLResponse)
async def mypage(request: Request):
    if not logged_in_user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("myinfo.html", {
        "request": request,
        "logged_in_user": logged_in_user,
        "user_info": None
    })

@app.post("/myinfo", response_class=HTMLResponse)
async def update_user_info(request: Request, password: str = Form(...)):
    # 현재 로그인된 사용자 정보 확인
    user = await users_collection.find_one({"username": logged_in_user})
    
    if not user:
        return templates.TemplateResponse("myinfo.html", {
            "request": request,
            "logged_in_user": logged_in_user,
            "user_info": None,
            "error_message": "User not found. Please log in again."
        })
    
    # 비밀번호 검증
    if pwd_context.verify(password, user["password"]):
        # 비밀번호가 맞으면, detail.html로 리디렉션
        return RedirectResponse(url="/detail", status_code=303)
    else:
        return templates.TemplateResponse("myinfo.html", {
            "request": request,
            "logged_in_user": logged_in_user,
            "user_info": None,
            "error_message": "Incorrect password. Please try again."
        })

# 사용자 상세 페이지 (detail.html 페이지 렌더링)
@app.get("/detail", response_class=HTMLResponse)
async def details_page(request: Request):
    try:
        user = await users_collection.find_one({"username": logged_in_user})
        if not user:
            return RedirectResponse(url="/login")

        # 템플릿 렌더링
        return templates.TemplateResponse("detail.html", {
            "request": request,
            "user": user,
            "logged_in_user": logged_in_user
        })

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 정보 수정 페이지
@app.get("/edit", response_class=HTMLResponse)
async def edit_user_info(request: Request):
    if not logged_in_user:
        return RedirectResponse(url="/login")
    
    user = await users_collection.find_one({"username": logged_in_user})
    if not user:
        return RedirectResponse(url="/login")
    
    # 카테고리 목록과 사용자의 선호 카테고리를 넘겨줌
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "user": user,
        "categories": categories_list
    })

# 정보 수정 처리
@app.post("/edit", response_class=HTMLResponse)
async def update_user_info(request: Request, selected_categories: list = Form(...)):
    if not logged_in_user:
        return RedirectResponse(url="/login")
    
    # 사용자의 선호 카테고리 업데이트
    result = await users_collection.update_one(
        {"username": logged_in_user},
        {"$set": {"preferences": selected_categories}}
    )
    
    if result.modified_count == 1:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "error_message": "정보 수정에 실패했습니다.",
    })

@app.get("/nan")
async def nan_endpoint():
    return {"message": "This is the /nan endpoint"}

@app.get("/이미지 정보 없음")
async def image_info_not_found():
    return {"message": "No image information available"}

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, keyword: Optional[str] = Query(None)):
    if not keyword:
        return templates.TemplateResponse("main.html", {"request": request, "error": "검색어를 입력하세요."})

    try:
        # KMeans 추천 시스템 로드
        recommender = KMeans.KeywordClusterRecommender.load_recommender(
            './models/keyword_recommender.pkl'
        )

        # KMeans 기반 추천 실행
        kmeans_recommendations = recommender.recommend_within_cluster_by_keyword(keyword, top_n=10)

        # 모든 상품을 하나의 리스트로 통합
        all_products = []
        for rec in kmeans_recommendations:
            # 대표 상품 추가
            if "target_product" in rec:
                # 가격을 float로 변환하여 저장
                product = rec["target_product"]
                try:
                    product['price'] = float(str(product['price']).replace(',', ''))
                except (ValueError, TypeError):
                    product['price'] = 0
                all_products.append(product)

            # 추천 상품들 추가
            if "recommendations" in rec:
                for product in rec["recommendations"]:
                    try:
                        product['price'] = float(str(product['price']).replace(',', ''))
                    except (ValueError, TypeError):
                        product['price'] = 0
                    all_products.append(product)

        # 중복 제거
        unique_products = list({product['url']: product for product in all_products}.values())

        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "keyword": keyword,
                "products": unique_products
            }
        )
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "keyword": keyword,
                "error": "검색 결과를 불러오는 중 오류가 발생했습니다.",
                "products": []
            }
        )
log_collection = users_db.product_click_logs

# 로그 데이터 모델
class ProductClickLog(BaseModel):
    broadcast_time: str
    title: str
    url: str
    image_url: str
    price: int
    timestamp: str

@app.post("/log_product_click")
async def log_product_click(log: ProductClickLog):
    # MongoDB에 로그 데이터 저장
    log_data = {
        "broadcast_time": log.broadcast_time,
        "title": log.title,
        "url": log.url,
        "image_url": log.image_url,
        "price": log.price,
        "timestamp": log.timestamp,
        "created_at": datetime.utcnow()  # 로그 저장 시점
    }
    log_collection.insert_one(log_data)
    return {"message": "로그 저장 완료", "data": log_data}

# uvicorn을 통해 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7777)