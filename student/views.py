from django.shortcuts import render, redirect, reverse, get_object_or_404
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from teacher import models as TMODEL
from exam.models import ExamSession, ProctoringEvent, SuspiciousActivity, Course
import cv2
import torch
from django.utils import timezone
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
import os
import threading


# for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return render(request, "student/studentclick.html")


def student_signup_view(request):
    userForm = forms.StudentUserForm()
    studentForm = forms.StudentForm()
    mydict = {"userForm": userForm, "studentForm": studentForm}
    if request.method == "POST":
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            student = studentForm.save(commit=False)
            student.user = user
            student.save()
            my_student_group = Group.objects.get_or_create(name="STUDENT")
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect("studentlogin")
    return render(request, "student/studentsignup.html", context=mydict)


def is_student(user):
    return user.groups.filter(name="STUDENT").exists()


# @login_required(login_url="studentlogin")
# @user_passes_test(is_student)
# @require_http_methods(["GET", "POST"])
# def logout_view(request):
#     logout(request)
#     return redirect("studentlogin")


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict = {
        "total_course": QMODEL.Course.objects.all().count(),
        "total_question": QMODEL.Question.objects.all().count(),
    }
    return render(request, "student/student_dashboard.html", context=dict)


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/student_exam.html", {"courses": courses})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def take_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    total_questions = QMODEL.Question.objects.all().filter(course=course).count()
    questions = QMODEL.Question.objects.all().filter(course=course)
    total_marks = 0
    for q in questions:
        total_marks = total_marks + q.marks

    return render(
        request,
        "student/take_exam.html",
        {
            "course": course,
            "total_questions": total_questions,
            "total_marks": total_marks,
        },
    )


# @login_required(login_url='studentlogin')
# @user_passes_test(is_student)
# def start_exam_view(request,pk):
#     course=QMODEL.Course.objects.get(id=pk)
#     questions=QMODEL.Question.objects.all().filter(course=course)
#     if request.method=='POST':
#         pass
#     response= render(request,'student/start_exam.html',{'course':course,'questions':questions})
#     response.set_cookie('course_id',course.id)
#     return response


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get("course_id") is not None:
        course_id = request.COOKIES.get("course_id")
        course = QMODEL.Course.objects.get(id=course_id)

        total_marks = 0
        questions = QMODEL.Question.objects.all().filter(course=course)
        for i in range(len(questions)):

            selected_ans = request.COOKIES.get(str(i + 1))
            actual_answer = questions[i].answer
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
        student = models.Student.objects.get(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks = total_marks
        result.exam = course
        result.student = student
        result.save()

        return HttpResponseRedirect("view-result")


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def view_result_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/view_result.html", {"courses": courses})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def check_marks_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results = QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, "student/check_marks.html", {"results": results})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_marks_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/student_marks.html", {"courses": courses})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def start_exam_view(request, pk):
    try:
        # Get the course and student details
        course = get_object_or_404(QMODEL.Course, id=pk)
        questions = QMODEL.Question.objects.filter(course=course)
        student = get_object_or_404(models.Student, user_id=request.user.id)

        # Start a new exam session for proctoring
        session = ExamSession.objects.create(
            student=student, course=course, start_time=timezone.now(), is_active=True
        )

        # Log the proctoring event that the exam has started
        ProctoringEvent.objects.create(
            session=session,
            event_type="Exam Started",
            description=f"Exam for {course.course_name} started by {student.user.username}.",
        )

        # Start the proctoring in a separate thread
        proctoring_thread = threading.Thread(target=run_proctoring, args=(session,))
        proctoring_thread.start()

        # Render the start exam page with context data
        response = render(
            request,
            "student/start_exam.html",
            {"course": course, "questions": questions, "session": session},
        )
        response.set_cookie("course_id", course.id)
        response.set_cookie("session_id", session.id)
        return response

    except Exception as e:
        return render(request, "error_page.html", {"error_message": str(e)})


def run_proctoring(session):
    # Load the YOLO model locally
    model_path = "yolov5"  # Replace with the actual path where you saved YOLOv5
    model = torch.hub.load(model_path, "custom", path="yolov5s.pt", source="local")
    print("YOLO model loaded successfully.")

    # Capture webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Unable to access the webcam.")

    frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Apply YOLO model to the frame
        results = model(frame)

        # Detect multiple faces or objects
        detected_objects = results.pred[0]  # List of detections
        if len(detected_objects) > 1:
            # Log suspicious activity
            log_suspicious_activity(
                session,
                "Multiple Faces Detected",
                "Multiple faces detected during the exam.",
            )

        # Save the frame (optional for debugging)
        cv2.imwrite(f"/frame-images/frame_{frame_number}.jpg", frame)
        frame_number += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()


def log_suspicious_activity(session, activity_type, description):
    """Helper function to log suspicious activities."""
    SuspiciousActivity.objects.create(
        session=session, activity_type=activity_type, description=description
    )
    session.suspicious_activity_count += 1
    session.save()


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def log_proctoring_event_view(request, session_id, event_type, description):
    session = get_object_or_404(ExamSession, id=session_id)

    # Log the proctoring event
    ProctoringEvent.objects.create(
        session=session, event_type=event_type, description=description
    )

    return redirect(reverse("start_exam", args=[session.course.id]))


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def log_suspicious_activity_view(request, session_id, activity_type, description):
    session = get_object_or_404(ExamSession, id=session_id)

    # Record suspicious activity
    log_suspicious_activity(session, activity_type, description)

    return redirect(reverse("start_exam", args=[session.course.id]))
