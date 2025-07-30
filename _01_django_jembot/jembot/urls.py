from django.urls import path
from . import views
from . import auth_views

# namespace 지정
app_name = 'jembot'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/chat/', views.chat_api, name='chat_api'),
    
    # 인증 관련 URL
    path('login/', auth_views.google_login, name='login'),
    path('accounts/google/login/callback/', auth_views.google_callback, name='google_callback'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.user_profile, name='profile'),
    
    # 채팅 세션 관리
    path('api/sessions/', auth_views.chat_sessions, name='chat_sessions'),
    path('api/sessions/create/', auth_views.create_session, name='create_session'),
    path('api/sessions/<str:session_id>/history/', views.get_chat_history, name='get_chat_history'),
    path('api/sessions/<str:session_id>/delete/', views.delete_session, name='delete_session'),
    
    # 뉴스 및 주식 API
    path('api/news/', views.crawl_naver_news, name='news_api'),
    path('api/stock/', views.get_stock_info, name='stock_api'),
]