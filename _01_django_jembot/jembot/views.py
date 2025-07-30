from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from datetime import datetime

from .models import Custom_user, Nickname
from .utils2.main import run_langraph

# Create your views here.

def index(request):
    user = Custom_user.objects.get(id=1)
    nickname = user.nickname

    return render(request, "app/main.html", {"nickname": nickname})

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """RAG 챗봇 API 엔드포인트"""
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
        
        # RAG 챗봇 실행 (세션 ID 전달)
        print(f"RAG 챗봇 호출: level='{level}'")
        response = run_langraph(user_message, session_id, level)
        
        # 응답에서 실제 답변 추출
        if isinstance(response, dict):
            bot_message = response.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
        else:
            bot_message = str(response)
        
        # 현재 시간
        current_time = datetime.now().strftime("%H:%M")
        
        return JsonResponse({
            'success': True,
            'bot_message': bot_message,
            'timestamp': current_time,
            'level': level,
            'session_id': session_id  # 세션 ID 반환
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)
