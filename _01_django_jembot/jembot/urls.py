from django.urls import path
from . import views

# namespace 지정
app_name = 'jembot'



urlpatterns = [
  path('', views.index, name='index'),
  path('api/chat/', views.chat_api, name='chat_api'),
  ]