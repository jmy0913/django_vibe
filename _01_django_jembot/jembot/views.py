from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from pykrx import stock
import pandas as pd
import numpy as np

from .models import Custom_user, Nickname, ChatSession, ChatMessage
from .utils2.main import run_langraph

# 별칭(Alias) 맵
STOCK_ALIASES = {
    "네이버": "NAVER",
    "엘지": "LG",
    "지에스": "GS",
    "에스케이": "SK",
    "엔씨": "엔씨소프트",
    "엘지화학": "LG화학",
    "sk하이닉스": "SK하이닉스",
    "엘지에너지솔루션": "LG에너지솔루션",
}

def clean_html(html_string):
    """HTML 태그를 제거하고 텍스트만 반환합니다."""
    return BeautifulSoup(html_string, "html.parser").get_text()

def guess_category(title: str, description: str) -> str:
    """뉴스의 제목과 설명을 기반으로 카테고리를 추측합니다."""
    text = (title + " " + description).lower()
    if any(word in text for word in ["경제", "금융", "투자", "기업", "증시", "주식", "부동산"]):
        return "경제"
    elif any(word in text for word in ["기술", "ai", "인공지능", "반도체", "it", "테크", "과학"]):
        return "기술"
    elif any(word in text for word in ["정치", "정부", "대통령", "국회", "선거", "외교"]):
        return "정치"
    elif any(word in text for word in ["사회", "사건", "사고", "범죄", "교육", "노동"]):
        return "사회"
    elif any(word in text for word in ["문화", "예술", "영화", "음악", "연예", "방송"]):
        return "문화"
    elif any(word in text for word in ["스포츠", "축구", "야구", "농구", "올림픽"]):
        return "스포츠"
    else:
        return "기타"

def time_ago(pub_date: str) -> str:
    """RFC 1123 포맷의 날짜 문자열을 'n분 전'과 같은 상대 시간으로 변환합니다."""
    try:
        date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
        now = datetime.now(timezone.utc)
        diff = now - date_obj
        
        seconds = diff.total_seconds()
        days = diff.days
        
        if days >= 30:
            return f"{days // 30}달 전"
        if days >= 7:
            return f"{days // 7}주 전"
        if days > 0:
            return f"{days}일 전"
        if seconds >= 3600:
            return f"{int(seconds // 3600)}시간 전"
        if seconds >= 60:
            return f"{int(seconds // 60)}분 전"
        return "방금 전"
    except (ValueError, TypeError):
        return pub_date

def format_market_cap(cap):
    """시가총액을 '조'와 '억' 단위로 변환합니다."""
    if not isinstance(cap, (int, float, np.number)):
        return "N/A"
    
    if cap is None or cap == 0:
        return "N/A"
    
    cap = float(cap)
    trillion = int(cap // 1_0000_0000_0000)
    billion = int((cap % 1_0000_0000_0000) // 1_0000_0000)
    
    if trillion > 0 and billion > 0:
        return f"{trillion}조 {billion}억"
    elif trillion > 0:
        return f"{trillion}조"
    elif billion > 0:
        return f"{billion}억"
    else:
        return f"{int(cap // 1_0000)}만"

# Create your views here.

@login_required
def index(request):
    """메인 페이지 - 로그인 필요"""
    try:
        nickname = request.user.nickname.nickname if hasattr(request.user, 'nickname') else request.user.username
    except:
        nickname = request.user.username
    
    return render(request, "app/main.html", {"nickname": nickname, "user": request.user})

# User 객체를 직렬화할 때 필요한 필드만 딕셔너리 형태로 변환
def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'profile_picture': user.profile_picture,
        'signup_at': user.signup_at.strftime('%Y-%m-%d %H:%M:%S')  # 날짜 형식 지정
    }


@require_http_methods(["POST"])
@login_required
def chat_api(request):
    """RAG 챗봇 API 엔드포인트 - 로그인 필요"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        level = data.get('level', 'basic')  # basic, intermediate, advanced
        session_id = data.get('session_id', '')  # 세션 ID 받기
        chat_history = data.get('chat_history', [])  # 대화 기록 받기
        
        # 디버깅용 로그
        print(f"받은 데이터: message='{user_message}', level='{level}', session_id='{session_id}'")
        print(f"대화 기록 길이: {len(chat_history)}")
        
        if not user_message:
            return JsonResponse({'error': '메시지가 없습니다.'}, status=400)
        
        # 세션 ID가 없으면 새로 생성
        if not session_id:
            session_id = str(uuid.uuid4())
            # 새 세션 생성
            chat_session = ChatSession.objects.create(
                user=request.user,
                session_id=session_id,
                title=user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
        else:
            # 기존 세션 가져오기
            try:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
        
        # 사용자 메시지 저장
        ChatMessage.objects.create(
            session=chat_session,
            message_type='user',
            content=user_message
        )
        
        # DB에서 채팅 히스토리 가져오기 (최근 20개 메시지만)
        db_chat_history = []
        messages = ChatMessage.objects.filter(session=chat_session).order_by('-timestamp')[:20]
        # 시간순으로 다시 정렬 (오래된 것부터)
        messages = reversed(messages)
        
        for msg in messages:
            if msg.message_type == 'user':
                db_chat_history.append({"role": "user", "content": msg.content})
            else:
                db_chat_history.append({"role": "assistant", "content": msg.content})
        
        # RAG 챗봇 실행 (세션 ID, 레벨, 대화 히스토리 전달)
        print(f"RAG 챗봇 호출: level='{level}', session_id='{session_id}', history_length={len(db_chat_history)}")
        response = run_langraph(user_message, session_id, level, db_chat_history)
        
        # 응답에서 실제 답변 추출
        if isinstance(response, dict):
            bot_message = response.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
        else:
            bot_message = str(response)
        
        # 봇 메시지 저장
        ChatMessage.objects.create(
            session=chat_session,
            message_type='bot',
            content=bot_message
        )
        
        # 세션 업데이트 시간 갱신
        chat_session.save()
        
        # 현재 시간
        current_time = datetime.now().strftime("%H:%M")
        
        return JsonResponse({
            'success': True,
            'bot_message': bot_message,
            'timestamp': current_time,
            'level': level,
            'session_id': session_id,  # 세션 ID 반환,
            'user': user_to_dict(request.user)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)



@login_required
def get_chat_history(request, session_id):
    """특정 세션의 채팅 히스토리 가져오기"""
    try:
        chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
        messages = ChatMessage.objects.filter(session=chat_session).order_by('timestamp')
        
        history = []
        for msg in messages:
            history.append({
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'session_title': chat_session.title,
            'history': history
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_session(request, session_id):
    """채팅 세션 삭제"""
    try:
        chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
        chat_session.is_active = False
        chat_session.save()
        
        return JsonResponse({'success': True})
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_stock_info(request):
    """
    회사명을 받아 주식 정보를 조회하고 JSON으로 반환하는 API 뷰.
    yfinance를 사용하여 상세 정보를 추가로 가져옵니다.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            company_name = data.get('query', '').strip()
            period = data.get('period', '1m') # 기본값 1개월

            if not company_name:
                return JsonResponse({'success': False, 'error': '기업명을 입력해주세요.'})

            # KRX 티커 정보 로드 및 캐싱
            if 'krx_tickers' not in get_stock_info.__dict__:
                latest_day_for_map = stock.get_nearest_business_day_in_a_week()
                kospi = stock.get_market_ticker_list(date=latest_day_for_map, market="KOSPI")
                kosdaq = stock.get_market_ticker_list(date=latest_day_for_map, market="KOSDAQ")
                tickers = kospi + kosdaq
                name_to_code = {stock.get_market_ticker_name(ticker): ticker for ticker in tickers}
                get_stock_info.krx_tickers = name_to_code
                print(f"KRX 티커 정보 로드 완료. ({len(tickers)}개 종목)")

            name_to_code = get_stock_info.krx_tickers
            
            # 스마트 검색 로직
            search_term = company_name.lower().replace(" ", "")
            if search_term in STOCK_ALIASES:
                company_name = STOCK_ALIASES[search_term]

            # 정확한 이름으로 코드 찾기
            found_code = None
            found_name = None
            for name, code in name_to_code.items():
                if name.lower().replace(" ", "") == company_name.lower().replace(" ", ""):
                    found_code = code
                    found_name = name
                    break
            
            if not found_code:
                # 일치하는 항목이 없으면, 제안 찾기 (부분 일치)
                similar_names = [name for name in name_to_code.keys() if company_name in name]
                if similar_names:
                    error_message = f"정확한 기업명을 입력해주세요.\n혹시 이거 찾으세요?: {', '.join(similar_names[:3])}"
                else:
                    error_message = "해당 기업명은 상장기업이 아닙니다."
                return JsonResponse({"success": False, "error": error_message})
            
            code = found_code
            company_name = found_name # 공식 명칭으로 업데이트
            
            # yfinance Ticker 객체 생성
            latest_day = stock.get_nearest_business_day_in_a_week()
            kospi_tickers = stock.get_market_ticker_list(date=latest_day, market="KOSPI")
            
            is_kospi = code in kospi_tickers
            yahoo_code = f"{code}.KS" if is_kospi else f"{code}.KQ"
            
            # yfinance 상세 정보 조회
            info = {}
            try:
                ticker = yf.Ticker(yahoo_code)
                info = ticker.info
            except Exception as e:
                print(f"yfinance ticker.info 조회 중 오류 발생: {e}")

            # 기본 정보 계산용 데이터 (항상 1년치)
            today = datetime.today()
            one_year_ago = today - timedelta(days=365)
            history_df = yf.download(yahoo_code, start=one_year_ago, end=today + timedelta(days=1), progress=False, auto_adjust=True)

            if history_df.empty:
                return JsonResponse({"success": False, "error": "주가 데이터를 가져올 수 없습니다."})
            
            # multi-level column 처리
            full_close_series = history_df['Close'].iloc[:, 0] if isinstance(history_df['Close'], pd.DataFrame) else history_df['Close']
            full_high_series = history_df['High'].iloc[:, 0] if isinstance(history_df['High'], pd.DataFrame) else history_df['High']
            full_low_series = history_df['Low'].iloc[:, 0] if isinstance(history_df['Low'], pd.DataFrame) else history_df['Low']
            full_volume_series = history_df['Volume'].iloc[:, 0] if isinstance(history_df['Volume'], pd.DataFrame) else history_df['Volume']
            
            # 52주 최고/최저 및 등락률 등 계산
            fifty_two_week_high = full_high_series.max()
            fifty_two_week_low = full_low_series.min()
            latest_close = full_close_series.iloc[-1]
            previous_close = full_close_series.iloc[-2] if len(full_close_series) > 1 else latest_close
            price_change = latest_close - previous_close
            change_percent = (price_change / previous_close) * 100 if previous_close != 0 else 0

            # 차트용 데이터
            if period == '1d':
                chart_df = yf.download(yahoo_code, period="1d", interval="15m", progress=False, auto_adjust=True)
                chart_df.index = chart_df.index.strftime('%H:%M')
            else:
                period_map = {'1w': 7, '1m': 30, '1y': 365}
                start_date = today - timedelta(days=period_map.get(period, 30))
                chart_df = history_df[history_df.index >= pd.to_datetime(start_date)]
                chart_df.index = chart_df.index.strftime('%m-%d')
            
            chart_df = chart_df.reset_index()
            chart_close_series = chart_df['Close'].iloc[:, 0] if isinstance(chart_df['Close'], pd.DataFrame) else chart_df['Close']
            
            # 데이터 값 안전하게 가져오기
            latest_price_val = info.get('currentPrice') if info.get('currentPrice') not in [None, 0] else latest_close
            volume_val = info.get('volume') if info.get('volume') not in [None, 0] else full_volume_series.iloc[-1]
            day_high_val = info.get('dayHigh') if info.get('dayHigh') not in [None, 0] else full_high_series.iloc[-1]
            day_low_val = info.get('dayLow') if info.get('dayLow') not in [None, 0] else full_low_series.iloc[-1]
            
            # PER/PBR 또는 대체 정보 구성
            per_label, per_value = "PER", info.get('trailingPE')
            if per_value is None:
                per_label, per_value = "Forward P/E", info.get('forwardPE')
                if per_value is None:
                    per_label = "EPS"
                    per_value = info.get('trailingEps')

            pbr_label, pbr_value = "PBR", info.get('priceToBook')
            if pbr_value is None:
                pbr_label = "배당수익률"
                dividend_yield = info.get('dividendYield')
                pbr_value = f"{dividend_yield * 100:.2f}%" if dividend_yield is not None else None

            response_data = {
                'success': True,
                'companyName': info.get('shortName', company_name),
                'code': yahoo_code,
                'period': period,
                'latestPrice': f"{latest_price_val:,.0f}",
                'priceChange': f"{price_change:+,.0f}",
                'changePercent': f"{change_percent:+.2f}",
                
                'marketCap': format_market_cap(info.get('marketCap')),
                'volume': f"{volume_val:,d}주",
                'fiftyTwoWeekHigh': f"₩{fifty_two_week_high:,.0f}",
                'fiftyTwoWeekLow': f"₩{fifty_two_week_low:,.0f}",
                
                'per_label': per_label,
                'per_value': f"{per_value:.2f}" if isinstance(per_value, (int, float)) else "N/A",
                'pbr_label': pbr_label,
                'pbr_value': pbr_value if pbr_value is not None else "N/A",

                'dayHigh': f"₩{day_high_val:,.0f}",
                'dayLow': f"₩{day_low_val:,.0f}",
                
                'chartData': {
                    'labels': chart_df.iloc[:, 0].tolist(),
                    'data': chart_close_series.tolist()
                }
            }
            return JsonResponse(response_data)

        except Exception as e:
            print(f"주식 정보 조회 중 오류 발생: {str(e)}")
            return JsonResponse({'success': False, 'error': f'서버 오류가 발생했습니다: {e}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def crawl_naver_news(request):
    """네이버 뉴스 API를 사용해서 뉴스 검색"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            search_query = data.get('query', '')

            if not settings.NAVER_CLIENT_ID or settings.NAVER_CLIENT_ID == "YOUR_CLIENT_ID":
                raise ValueError("네이버 API Client ID가 설정되지 않았습니다.")
            if not settings.NAVER_CLIENT_SECRET or settings.NAVER_CLIENT_SECRET == "YOUR_CLIENT_SECRET":
                raise ValueError("네이버 API Client Secret이 설정되지 않았습니다.")

            url = 'https://openapi.naver.com/v1/search/news.json'
            headers = {
                "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET
            }
            params = {
                'query': search_query,
                'display': 10,  # 가져올 뉴스 개수
                'start': 1,
                'sort': 'date'  # 최신순 정렬
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # 오류 발생 시 예외 발생

            news_data = response.json()
            
            if 'items' in news_data and news_data['items']:
                title_matches = []
                other_matches = []

                for item in news_data['items']:
                    title = clean_html(item['title'])
                    description = clean_html(item['description'])
                    
                    news_item = {
                        'title': title,
                        'content': description,
                        'link': item['originallink'],
                        'press': guess_category(title, description),
                        'time': time_ago(item.get('pubDate', ''))
                    }

                    # 제목에 검색어가 포함된 경우 우선순위 리스트에 추가
                    if search_query.lower() in title.lower():
                        title_matches.append(news_item)
                    else:
                        other_matches.append(news_item)
                
                # 두 리스트를 합쳐 최종 결과 생성 (제목 일치 항목이 위로)
                news_list = title_matches + other_matches
                
                print(f"API 호출 성공: {len(title_matches)}개 제목 일치, 총 {len(news_list)}개 정렬")

                if not news_list:
                    # API 결과 자체가 없는 경우
                    news_list = [{'title': f'"{search_query}"에 대한 뉴스 결과가 없습니다.', 'content': '다른 검색어로 다시 시도해주세요.', 'link': '#', 'press': '시스템', 'time': '방금전'}]
                    return JsonResponse({'success': True, 'news': news_list, 'no_results': True})

                return JsonResponse({'success': True, 'news': news_list})
            else:
                # 검색 결과가 없을 때의 메시지
                news_list = [{'title': f'"{search_query}"에 대한 뉴스 검색 결과가 없습니다.', 'content': '다른 검색어로 다시 시도해주세요.', 'link': '#', 'press': '시스템', 'time': '방금전'}]
                return JsonResponse({'success': True, 'news': news_list, 'no_results': True})

        except ValueError as e:
            print(f"API 키 설정 오류: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
        except requests.exceptions.RequestException as e:
            print(f"API 호출 오류: {e}")
            error_data = e.response.json() if e.response else {}
            return JsonResponse({'success': False, 'error': f"API 호출에 실패했습니다: {error_data.get('errorMessage', str(e))}"})
        except Exception as e:
            print(f"알 수 없는 오류 발생: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
