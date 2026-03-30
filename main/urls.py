from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # студент
    path('student/', views.student_schedule, name='student_schedule'),
    path('student/progress/', views.student_progress, name='student_progress'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # QR
    path('student/scan/<int:schedule_id>/', views.scan_qr, name='scan_qr'),
    path('student/qr-submit/<int:schedule_id>/', views.qr_submit, name='qr_submit'),

    # преподаватель
    path('teacher/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/journal/', views.teacher_journal, name='teacher_journal'),
    path('teacher/attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),

    # админ
    path('admin/', admin.site.urls),
]