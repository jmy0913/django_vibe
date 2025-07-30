from django.db import models

# Create your models here.


# 모델 생성
class Custom_user(models.Model):
    id_key = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    signup_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Nickname(models.Model):
    user = models.OneToOneField(Custom_user, on_delete=models.CASCADE, related_name='nickname')
    nickname = models.CharField(max_length=100)

    def __str__(self):
        return self.nickname
