# root계정으로 접속

# 사용자 django/django 생성
create user if not exists 'jembot'@'%' identified by 'jembot';

# djangodb 데이터베이스 생성
# - 인코딩 utf8mb4 (다국어/이모지 텍스트 지원)
# - 정렬방식 utf8mb4_unicode_ci (대소문자 구분없음)
create database if not exists jembotdb character set utf8mb4 collate utf8mb4_unicode_ci;

# django 계정 권한 부여
grant all privileges on jembotdb.* to 'jembot'@'%';
# 변경된 권한 설정을 서버 메모리에 즉시 로드하여 적용합니다.
flush privileges;