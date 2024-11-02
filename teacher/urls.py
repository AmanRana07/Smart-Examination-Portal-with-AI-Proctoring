from django.urls import path
from teacher import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("teacherclick", views.teacherclick_view),
    path(
        "teacherlogin",
        LoginView.as_view(template_name="teacher/teacherlogin.html"),
        name="teacherlogin",
    ),
    path("teachersignup", views.teacher_signup_view, name="teachersignup"),
    path("teacher-dashboard", views.teacher_dashboard_view, name="teacher-dashboard"),
    path("teacher-exam", views.teacher_exam_view, name="teacher-exam"),
    path("teacher-add-exam", views.teacher_add_exam_view, name="teacher-add-exam"),
    path("teacher-view-exam", views.teacher_view_exam_view, name="teacher-view-exam"),
    path("delete-exam/<int:pk>", views.delete_exam_view, name="delete-exam"),
    path("teacher-question", views.teacher_question_view, name="teacher-question"),
    path(
        "question-format",
        views.teacher_question_format_view,
        name="teacher-question-format",
    ),
    path(
        "teacher-add-question",
        views.teacher_add_question_view,
        name="teacher-add-question",
    ),
    path(
        "teacher-view-question",
        views.teacher_view_question_view,
        name="teacher-view-question",
    ),
    path("see-question/<int:pk>", views.see_question_view, name="see-question"),
    path(
        "remove-question/<int:pk>", views.remove_question_view, name="remove-question"
    ),
    path(
        "edit-course/<int:course_id>/",
        views.teacher_edit_course,
        name="edit-exam-course",
    ),
    path(
        "teacher-add-multiple-questions/",
        views.teacher_add_multiple_questions_view,
        name="teacher-add-multiple-questions",
    ),
    path(
        "download-questions-template/",
        views.download_questions_template,
        name="download-questions-template",
    ),
]
