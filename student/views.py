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
from exam.models import *
import cv2
import torch
from django.utils import timezone
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
import os
import threading
import base64
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from .models import StudentImage
from django.core.exceptions import ObjectDoesNotExist
import numpy as np
from django.http import JsonResponse
import time
import logging
from django.views.decorators.csrf import csrf_exempt
import json


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
        total_marks += q.marks

    return render(
        request,
        "student/take_exam.html",
        {
            "course": course,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "course_id": pk,  # Pass the course ID to the template
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
        student = Student.objects.get(user_id=request.user.id)
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
    student = Student.objects.get(user_id=request.user.id)
    results = QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, "student/check_marks.html", {"results": results})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_marks_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/student_marks.html", {"courses": courses})


# @login_required(login_url="studentlogin")
# @user_passes_test(is_student)
# def start_exam_view(request, pk):
#     try:
#         # Get the course and student details
#         course = get_object_or_404(QMODEL.Course, id=pk)
#         questions = QMODEL.Question.objects.filter(course=course)
#         student = get_object_or_404(models.Student, user_id=request.user.id)

#         # Start a new exam session for proctoring
#         session = ExamSession.objects.create(
#             student=student, course=course, start_time=timezone.now(), is_active=True
#         )

#         # Log the proctoring event that the exam has started
#         ProctoringEvent.objects.create(
#             session=session,
#             event_type="Exam Started",
#             description=f"Exam for {course.course_name} started by {student.user.username}.",
#         )

#         # Start the proctoring in a separate thread
#         proctoring_thread = threading.Thread(target=run_proctoring, args=(session,))
#         proctoring_thread.start()

#         # Pass 'duration' to the template, ensuring JavaScript gets the right value
#         context = {
#             "course": course,
#             "questions": questions,
#             "session": session,
#             "duration": course.duration_minutes,  # Add the exam duration in minutes
#         }

#         # Render the start exam page with context data
#         response = render(request, "student/start_exam.html", context)
#         response.set_cookie("course_id", course.id)
#         response.set_cookie("session_id", session.id)
#         return response

#     except Exception as e:
#         return render(request, "error_page.html", {"error_message": str(e)})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def start_exam_view(request, pk):
    try:
        # Retrieve the exam session from the cookie
        session_id = request.COOKIES.get("session_id")
        if not session_id:
            return HttpResponseBadRequest("Session ID is missing.")

        session = get_object_or_404(ExamSession, id=session_id)

        # Check if the session is for the correct course
        if session.course.id != pk:
            return HttpResponseBadRequest("Course ID mismatch.")

        # Get the course and student details
        course = get_object_or_404(QMODEL.Course, id=pk)
        questions = QMODEL.Question.objects.filter(course=course)

        try:
            exam_session = ExamSession.objects.get(
                course_id=course.id, student=request.user.student
            )
            if exam_session.cancellation_flag:
                return redirect("exam-cancellation-page")
            if exam_session.reload_detected:
                return redirect("exam-cancellation-page")
        except ExamSession.DoesNotExist:
            return HttpResponseBadRequest("Exam session does not exist.")

        # Log the proctoring event that the exam has started
        ProctoringEvent.objects.create(
            session=session,
            event_type="Exam Started",
            description=f"Exam for {course.course_name} started by {session.student.user.username}.",
        )

        # Start the proctoring in a separate thread
        proctoring_thread = threading.Thread(target=run_proctoring, args=(session,))
        proctoring_thread.start()

        # Render the start exam page with context data
        response = render(
            request,
            "student/start_exam.html",
            {
                "course": course,
                "questions": questions,
                "session": session,
                "duration": course.duration_minutes,
            },
        )
        return response

    except Exception as e:
        return render(request, "error_page.html", {"error_message": str(e)})


# def run_proctoring(session):
#     # Load the YOLO model locally
#     model_path = "yolov5"  # Replace with the actual path where you saved YOLOv5
#     model = torch.hub.load(model_path, "custom", path="yolov5s.pt", source="local")
#     print("YOLO model loaded successfully.")

#     # Capture webcam
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         raise Exception("Unable to access the webcam.")

#     frame_number = 0

#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break

#         # Apply YOLO model to the frame
#         results = model(frame)

#         # Detect multiple faces or objects
#         detected_objects = results.pred[0]  # List of detections
#         if len(detected_objects) > 1:
#             # Log suspicious activity
#             log_suspicious_activity(
#                 session,
#                 "Multiple Faces Detected",
#                 "Multiple faces detected during the exam.",
#             )

#         # Save the frame (optional for debugging)
#         cv2.imwrite(f"/frame-images/frame_{frame_number}.jpg", frame)
#         frame_number += 1

#         if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to quit
#             break

#     cap.release()
#     cv2.destroyAllWindows()


# def log_suspicious_activity(session, activity_type, description):
#     """Helper function to log suspicious activities."""
#     SuspiciousActivity.objects.create(
#         session=session, activity_type=activity_type, description=description
#     )
#     session.suspicious_activity_count += 1
#     session.save()


# @login_required(login_url="studentlogin")
# @user_passes_test(is_student)
# def log_proctoring_event_view(request, session_id, event_type, description):
#     session = get_object_or_404(ExamSession, id=session_id)

#     # Log the proctoring event
#     ProctoringEvent.objects.create(
#         session=session, event_type=event_type, description=description
#     )

#     return redirect(reverse("start_exam", args=[session.course.id]))


# @login_required(login_url="studentlogin")
# @user_passes_test(is_student)
# def log_suspicious_activity_view(request, session_id, activity_type, description):
#     session = get_object_or_404(ExamSession, id=session_id)

#     # Record suspicious activity
#     log_suspicious_activity(session, activity_type, description)

#     return redirect(reverse("start_exam", args=[session.course.id]))

# @login_required(login_url="studentlogin")
# @user_passes_test(is_student)
# def capture_image(request, course_id):
#     if request.method == 'POST':
#         image_data = request.POST.get('image_data')
#         format, imgstr = image_data.split(';base64,')
#         ext = format.split('/')[-1]
#         data = ContentFile(base64.b64decode(imgstr), name=f'{request.user.username}.{ext}')

#         # Ensure course_id is retrieved correctly from the URL or cookies
#         if not course_id:
#             course_id = request.COOKIES.get("course_id")

#         if not course_id:
#             # Handle the case where course_id is still None
#             return HttpResponseBadRequest("Course ID is missing.")

#         try:
#             # Check if an image already exists for the user
#             student_image = StudentImage.objects.get(user=request.user)
#             # If it exists, update the existing image
#             student_image.image = data
#             student_image.save()
#         except StudentImage.DoesNotExist:
#             # If it does not exist, create a new image entry
#             student_image = StudentImage(user=request.user, image=data)
#             student_image.save()

#         # Redirect to the take-exam view with the correct course_id
#         return redirect('take-exam', pk=course_id)

#     return render(request, 'student/capture_image.html', {"course_id": course_id})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def check_exam_status(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id)
    return JsonResponse(
        {"is_active": session.is_active, "cancellation_flag": session.cancellation_flag}
    )


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def monitor_exam_cancellation_view(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id)

    while session.is_active:
        session.refresh_from_db()
        if session.cancellation_flag:
            return redirect("exam-cancellation-page")
        time.sleep(1)

    return redirect("exam-completion-page")


def run_proctoring(session):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Unable to access the webcam.")

    # Retrieve all stored images for the student
    student_images = StudentImage.objects.filter(user=session.student.user)
    training_images = []
    labels = []

    for idx, student_image in enumerate(student_images):
        stored_image = cv2.imread(student_image.image.path)
        stored_image_gray = cv2.cvtColor(stored_image, cv2.COLOR_BGR2GRAY)
        training_images.append(stored_image_gray)
        labels.append(idx)  # Assigning a label to each image

    # Initialize face detector and face recognizer
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Train the recognizer with all stored images
    recognizer.train(training_images, np.array(labels))

    alerts_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray_frame, scaleFactor=1.1, minNeighbors=5
        )

        for x, y, w, h in faces:
            roi_gray = gray_frame[y : y + h, x : x + w]
            label, confidence = recognizer.predict(roi_gray)

            if confidence < 60:
                print("Face matched.")
            else:
                print("Face did not match. Cancelling exam...")
                alerts_count += 1
                log_suspicious_activity(
                    session,
                    "Face Mismatch Detected",
                    "The face in the current frame does not match the stored face.",
                )
                if alerts_count >= 3:
                    session.is_active = False
                    session.cancellation_flag = True
                    session.save()
                    cap.release()
                    cv2.destroyAllWindows()
                    cancel_exam(session)
                    return

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        time.sleep(15)  # Wait for 15 seconds before the next check

    cap.release()
    cv2.destroyAllWindows()


def log_suspicious_activity(session, activity_type, description):
    """Helper function to log suspicious activities."""
    SuspiciousActivity.objects.create(
        session=session, activity_type=activity_type, description=description
    )
    session.suspicious_activity_count += 1
    session.save()


def cancel_exam(session):
    ProctoringEvent.objects.create(
        session=session,
        event_type="Exam Cancelled",
        description="Exam was cancelled due to face mismatch.",
    )
    return redirect("exam-cancellation-page")


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def exam_cancellation_view(request):
    return render(
        request,
        "student/exam_cancellation.html",
        {"message": "Your exam has been cancelled due to suspicious activity."},
    )


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def log_proctoring_event_view(request, session_id, event_type, description):
    session = get_object_or_404(ExamSession, id=session_id)

    ProctoringEvent.objects.create(
        session=session, event_type=event_type, description=description
    )

    return redirect(reverse("start_exam", args=[session.course.id]))


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def log_suspicious_activity_view(request, session_id, activity_type, description):
    session = get_object_or_404(ExamSession, id=session_id)

    log_suspicious_activity(session, activity_type, description)

    return redirect(reverse("start_exam", args=[session.course.id]))


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def capture_image(request, course_id):
    if request.method == "POST":
        image_data = request.POST.get("image_data")
        format, imgstr = image_data.split(";base64,")
        ext = format.split("/")[-1]
        data = ContentFile(
            base64.b64decode(imgstr), name=f"{request.user.username}.{ext}"
        )

        if not course_id:
            course_id = request.COOKIES.get("course_id")

        if not course_id:
            return HttpResponseBadRequest("Course ID is missing.")

        # Retrieve or create the student image
        try:
            student_image = StudentImage.objects.get(user=request.user)
            student_image.image = data
            student_image.save()
            session, created = ExamSession.objects.get_or_create(
                student=request.user.student,
                course_id=course_id,
                defaults={"start_time": timezone.now(), "is_active": True},
            )
        except StudentImage.DoesNotExist:
            student_image = StudentImage(user=request.user, image=data)
            student_image.save()

        try:
            exam_session = ExamSession.objects.get(
                course_id=course_id, student=request.user.student
            )
            if exam_session.cancellation_flag:
                return redirect("exam-cancellation-page")
        except ExamSession.DoesNotExist:
            return HttpResponseBadRequest("Exam session does not exist.")

        # Create or retrieve the exam session for the course

        response = redirect("take-exam", pk=course_id)
        response.set_cookie("session_id", session.id)
        return response

    return render(request, "student/capture_image.html", {"course_id": course_id})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def compare_image_view(request):
    if request.method == "POST":
        # Get the session ID from the request
        session_id = request.POST.get("session_id")
        session = get_object_or_404(ExamSession, id=session_id)

        # Get the image data from the request
        image_data = request.POST.get("image_data")
        format, imgstr = image_data.split(";base64,")
        img_bytes = base64.b64decode(imgstr)

        # Convert the image data to a numpy array and then to a grayscale image
        np_arr = np.frombuffer(img_bytes, np.uint8)
        captured_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        captured_image_gray = cv2.cvtColor(captured_image, cv2.COLOR_BGR2GRAY)

        # Load the stored image from the database
        student_image = get_object_or_404(StudentImage, user=session.student.user)
        stored_image = cv2.imread(student_image.image.path)
        stored_image_gray = cv2.cvtColor(stored_image, cv2.COLOR_BGR2GRAY)

        # Initialize face recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        # Train the recognizer with the stored image
        recognizer.train([stored_image_gray], np.array([0]))

        # Perform face recognition on the captured image
        label, confidence = recognizer.predict(captured_image_gray)

        # Set a threshold for the confidence value
        match_threshold = 90  # Adjust this value based on your testing

        if confidence < match_threshold:
            return JsonResponse({"match": True, "Confidence": confidence})
        else:
            session.cancellation_flag = True
            session.save()
            return JsonResponse({"match": False, "Confidence": confidence})

    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def send_message_view(request):
    if request.method == "POST":
        session_id = request.POST.get("session_id")
        message_text = request.POST.get("message")
        session = get_object_or_404(ExamSession, id=session_id)
        sender = request.user

        message = ChatMessage.objects.create(
            session=session, sender=sender, message=message_text
        )

        return JsonResponse(
            {"status": "success", "message": "Message sent successfully"}
        )
    return JsonResponse({"status": "error", "message": "Invalid request method"})


def get_chat_history_view(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id)
    messages = ChatMessage.objects.filter(session=session).order_by("timestamp")
    chat_history = [
        {
            "sender": msg.sender.username,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for msg in messages
    ]

    return JsonResponse(chat_history, safe=False)


@csrf_exempt
def save_violation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        session_id = data.get("session_id")
        violation_message = data.get("violation_message")

        Violation.objects.create(
            session_id=session_id,
            user=request.user,
            violation_message=violation_message,
        )

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "failed"}, status=400)
