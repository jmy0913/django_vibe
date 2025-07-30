from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('api/crawl-news/', views.crawl_naver_news, name='crawl_news'),
    path('api/get-stock-info/', views.get_stock_info, name='get_stock_info'),
]
