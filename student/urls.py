from django.urls import path
from student import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("studentclick", views.studentclick_view, name="studentclick"),
    path(
        "studentlogin",
        LoginView.as_view(template_name="student/studentlogin.html"),
        name="studentlogin",
    ),
    path("studentsignup", views.student_signup_view, name="studentsignup"),
    path("student-dashboard", views.student_dashboard_view, name="student-dashboard"),
    path("student-exam", views.student_exam_view, name="student-exam"),
    path("take-exam/<int:pk>", views.take_exam_view, name="take-exam"),
    path("capture-image/<int:course_id>/", views.capture_image, name="capture-image"),
    path("start-exam/<int:pk>", views.start_exam_view, name="start-exam"),
    path("calculate-marks", views.calculate_marks_view, name="calculate-marks"),
    path("view-result", views.view_result_view, name="view-result"),
    path("check-marks/<int:pk>", views.check_marks_view, name="check-marks"),
    path("student-marks", views.student_marks_view, name="student-marks"),
    path(
        "log-proctoring-event/<int:session_id>/<str:event_type>/<str:description>/",
        views.log_proctoring_event_view,
        name="log_proctoring_event",
    ),
    path(
        "log-suspicious-activity/<int:session_id>/<str:activity_type>/<str:description>/",
        views.log_suspicious_activity_view,
        name="log_suspicious_activity",
    ),
    path(
        "check_exam_status/<int:session_id>/",
        views.check_exam_status,
        name="check_exam_status",
    ),
    path("compare-image/", views.compare_image_view, name="compare_image"),
    path('send-message/', views.send_message_view, name='send-message'),
    path('get-chat-history/<int:session_id>/', views.get_chat_history_view, name='get-chat-history'),
    path(
        "exam-cancellation/",
        views.exam_cancellation_view,
        name="exam-cancellation-page",
    ),
]
