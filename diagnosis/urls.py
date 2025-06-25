from django.urls import path
from . import views

app_name = 'diagnosis'

urlpatterns = [
    path('', views.index, name='index'),  # 시작 페이지
    path('survey/', views.survey, name='survey'),  # 설문 페이지
    path('submit_survey/', views.submit_survey, name='submit_survey'),  # 설문 응답 제출
    path('request_report/', views.request_report, name='request_report'), # 상세 결과 리포트 요청
    path('result/<str:result_id>/', views.result, name='result'),  # 결과 페이지 (결과 ID 포함)
    path('contact/', views.contact_view, name='contact'), # 문의하기 페이지
    path('start/', views.survey_start, name='survey_start'),  # 이메일 입력 페이지
    path('survey/<uuid:result_id>/', views.survey, name='survey'),  # 설문 페이지 (UUID 기반)
    path('result/<uuid:result_id>/', views.result, name='result'),  # 결과 페이지 (UUID 기반)
    path('retry/<uuid:result_id>/', views.retry_survey, name='retry_survey'),  # 다시 검사하기
]