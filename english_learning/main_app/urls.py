# main_app/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<int:course_id>/lessons/', views.course_lessons, name='course_lessons'),
    path('book_lesson/<int:lesson_id>/', views.book_lesson, name='book_lesson'),
    path('payment/<int:enrollment_id>/', views.payment, name='payment'),
    path('payment/process/<int:enrollment_id>/', views.payment_process, name='payment_process'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
    #admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # Views for managing enrollments
    path('add-enrollment/', views.add_enrollment, name='add_enrollment'),
    path('edit-enrollment/<int:enrollment_id>/', views.edit_enrollment, name='edit_enrollment'),
    path('delete-enrollment/<int:enrollment_id>/', views.delete_enrollment, name='delete_enrollment'),
    
    # Views for managing courses
    path('add-course/', views.add_course, name='add_course'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('add_lesson/', views.add_lesson, name='add_lesson'),

    # Views for managing bookings
    path('add-booking/', views.add_booking, name='add_booking'),
    path('edit-booking/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('delete-booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),
]

