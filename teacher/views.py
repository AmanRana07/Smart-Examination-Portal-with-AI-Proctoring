from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
import csv
import io
from django.http import HttpResponse
from collections import defaultdict
from django.db.models import Avg, F
import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages



# for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return render(request, "teacher/teacherclick.html")


def teacher_signup_view(request):
    userForm = forms.TeacherUserForm()
    teacherForm = forms.TeacherForm()
    mydict = {"userForm": userForm, "teacherForm": teacherForm}
    if request.method == "POST":
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name="TEACHER")
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect("teacherlogin")
    return render(request, "teacher/teachersignup.html", context=mydict)


def is_teacher(user):
    return user.groups.filter(name="TEACHER").exists()


from django.db.models import Avg, Count, Q


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    teacher = request.user
    teacher_courses = QMODEL.Course.objects.filter(creator=teacher)
    passing_mark = 40  # Set a passing mark threshold

    # Data for each graph
    course_names = [course.course_name for course in teacher_courses]

    # Average Marks per Course
    average_marks = [
        QMODEL.Result.objects.filter(exam=course).aggregate(avg_marks=Avg("marks"))[
            "avg_marks"
        ]
        or 0
        for course in teacher_courses
    ]

    # Exam Completion Rate per Course
    completion_rates = [
        QMODEL.Result.objects.filter(exam=course).count() for course in teacher_courses
    ]

    # Violation Counts per Course
    violations_counts = [
        QMODEL.Violation.objects.filter(session__course=course).count()
        for course in teacher_courses
    ]

    # Pass/Fail Rate per Course
    pass_counts = [
        QMODEL.Result.objects.filter(exam=course, marks__gte=passing_mark).count()
        for course in teacher_courses
    ]
    fail_counts = [
        QMODEL.Result.objects.filter(exam=course, marks__lt=passing_mark).count()
        for course in teacher_courses
    ]

    # Total Questions per Course
    question_counts = [
        QMODEL.Question.objects.filter(course=course).count()
        for course in teacher_courses
    ]

    context = {
        "total_course": teacher_courses.count(),
        "total_question": QMODEL.Question.objects.filter(
            course__in=teacher_courses
        ).count(),
        "total_student": SMODEL.Student.objects.filter(
            examsession__course__in=teacher_courses
        )
        .distinct()
        .count(),
        "course_names": course_names,
        "average_marks": average_marks,
        "completion_rates": completion_rates,
        "violations_counts": violations_counts,
        "pass_counts": pass_counts,
        "fail_counts": fail_counts,
        "question_counts": question_counts,
    }

    return render(request, "teacher/teacher_dashboard.html", context)


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request, "teacher/teacher_exam.html")


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_question_format_view(request):
    return render(request, "teacher/teacher_question_format.html")


@login_required(login_url="adminlogin")
@user_passes_test(is_teacher)
def teacher_add_multiple_questions_view(request):
    courses = QMODEL.Course.objects.filter(creator=request.user)

    if request.method == "POST":
        course_id = request.POST.get("courseID")
        csv_file = request.FILES.get("csv_file")

        if not csv_file or not csv_file.name.endswith(".csv"):
            messages.error(request, "File is not a CSV type or not uploaded")
            return redirect("teacher-add-multiple-questions")

        try:
            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string, delimiter=",")
            next(reader)  # Skip the header row if there is one

            errors = []  # To keep track of errors encountered
            for row in reader:
                if len(row) < 7:
                    errors.append("CSV file is missing required fields.")
                    continue  # Skip this row and continue with the next

                # Unpacking the row into variables
                question_text = row[0].strip().replace('"', "")
                option1 = row[1].strip().replace('"', "")
                option2 = row[2].strip().replace('"', "")
                option3 = row[3].strip().replace('"', "")
                option4 = row[4].strip().replace('"', "")
                correct_answer = row[5].strip().replace('"', "")
                marks = row[6].strip().replace('"', "")

                # Validate and cast marks
                try:
                    marks = int(marks)
                except ValueError:
                    errors.append(f"Invalid marks value for question: {question_text}")
                    continue  # Skip this question and continue

                # Validate answer choice
                if correct_answer not in ["Option1", "Option2", "Option3", "Option4"]:
                    errors.append(
                        f"Invalid answer choice for question: {question_text}"
                    )
                    continue  # Skip this question and continue

                # Create a new question object
                question = QMODEL.Question(
                    course_id=course_id,
                    question=question_text,
                    option1=option1,
                    option2=option2,
                    option3=option3,
                    option4=option4,
                    answer=correct_answer,
                    marks=marks,
                )
                question.save()

            if errors:
                messages.error(
                    request,
                    "Errors occurred while adding some questions: " + "; ".join(errors),
                )
            else:
                messages.success(request, "All questions added successfully!")

            return redirect("teacher-view-exam")  # Redirect after processing

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")

    return render(
        request, "teacher/teacher_multiple_question_type.html", {"courses": courses}
    )


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm = QFORM.CourseForm()
    if request.method == "POST":
        courseForm = QFORM.CourseForm(request.POST)
        if courseForm.is_valid():
            course = courseForm.save(commit=False)  # Don't save yet
            course.creator = request.user  # Set the creator to the current user
            course.save()  # Now save the course
        else:
            print("form is invalid")
        return HttpResponseRedirect("/teacher/teacher-view-exam")
    return render(request, "teacher/teacher_add_exam.html", {"courseForm": courseForm})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_edit_course(request, course_id):
    course = get_object_or_404(QMODEL.Course, id=course_id)
    if request.method == "POST":
        form = QFORM.CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect("teacher-view-exam")
    else:
        form = QFORM.CourseForm(instance=course)
    return render(request, "teacher/teacher_edit_course.html", {"form": form})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.filter(
        creator=request.user
    )  # Filter courses by the logged-in teacher
    return render(request, "teacher/teacher_view_exam.html", {"courses": courses})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def delete_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect("/teacher/teacher-view-exam")


@login_required(login_url="adminlogin")
def teacher_question_view(request):
    return render(request, "teacher/teacher_question.html")


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    user_courses = QMODEL.Course.objects.filter(creator=request.user)
    questionForm = QFORM.QuestionForm()
    questionForm.fields["courseID"].queryset = user_courses
    if request.method == "POST":
        questionForm = QFORM.QuestionForm(request.POST)
        questionForm.fields["courseID"].queryset = (
            user_courses  # Ensure the form filters courses on POST as well
        )
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            question.course = questionForm.cleaned_data["courseID"]
            question.save()
            return HttpResponseRedirect("/teacher/teacher-view-question")
        else:
            print("form is invalid")
        return HttpResponseRedirect("/teacher/teacher-view-question")
    return render(
        request, "teacher/teacher_add_question.html", {"questionForm": questionForm}
    )


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses = QMODEL.Course.objects.filter(
        creator=request.user
    )  # Filter courses by the logged-in teacher
    return render(request, "teacher/teacher_view_question.html", {"courses": courses})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def see_question_view(request, pk):
    questions = QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request, "teacher/see_question.html", {"questions": questions})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def remove_question_view(request, pk):
    question = QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect("/teacher/teacher-view-question")


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def download_questions_template(request):
    # Create a CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="questions_template.csv"'

    writer = csv.writer(response)
    # Write the header
    writer.writerow(
        [
            "question",
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_answer",
            "marks",
        ]
    )
    # You can add sample rows if needed
    writer.writerow(
        [
            '"What is the boiling point of water?"',
            '"90°C"',
            '"100°C"',
            '"80°C"',
            '"110°C"',
            '"Option2"',
            '"4"',
        ]
    )
    writer.writerow(
        [
            '"What is the capital of France?"',
            '"London"',
            '"Berlin"',
            '"Paris"',
            '"Madrid"',
            '"Option3"',
            '"3"',
        ]
    )
    writer.writerow(
        ['"What is 2 + 2?"', '"3"', '"4"', '"5"', '"6"', '"Option2"', '"2"']
    )

    return response


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_view_student_view(request):
    # Get the current teacher
    teacher = request.user

    # Fetch courses created by this teacher
    teacher_courses = QMODEL.Course.objects.filter(creator=teacher)

    # Get ExamSessions related to these courses
    exam_sessions = QMODEL.ExamSession.objects.filter(course__in=teacher_courses)

    # Get Results related to these courses through the exam field
    results = QMODEL.Result.objects.filter(exam__in=teacher_courses)

    # Prepare student data with marks for each course
    student_data = defaultdict(list)
    for result in results:
        student_data[result.student].append(
            {"course": result.exam.course_name, "marks": result.marks}
        )

    context = {
        "total_student": len(student_data),  # Unique students count
        "student_data": student_data,
    }
    return render(request, "teacher/teacher_student.html", context)


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def student_view(request):
    # Get the current teacher
    # Get the current teacher
    teacher = request.user

    # Fetch courses created by this teacher
    teacher_courses = QMODEL.Course.objects.filter(creator=teacher)

    # Get ExamSessions related to these courses
    exam_sessions = QMODEL.ExamSession.objects.filter(course__in=teacher_courses)

    # Get Results related to these courses through the exam field
    results = QMODEL.Result.objects.filter(exam__in=teacher_courses)

    # Prepare student data with marks for each course
    student_data = defaultdict(list)
    for result in results:
        student_data[result.student].append(
            {"course": result.exam.course_name, "marks": result.marks}
        )

    context = {
        "total_student": len(student_data),  # Unique students count
        "student_data": student_data,
    }
    return render(request, "teacher/teacher_view_student.html", context)


@login_required
@user_passes_test(is_teacher)
def teacher_view_student_marks(request, student_id):
    # Get the current teacher
    teacher = request.user

    # Fetch courses created by this teacher
    teacher_courses = QMODEL.Course.objects.filter(creator=teacher)

    # Get Results related to the specific student for the teacher's courses
    results = QMODEL.Result.objects.filter(
        exam__in=teacher_courses,  # Filter results by exams in teacher's courses
        student_id=student_id,  # Filter by the specific student ID
    )

    # Optionally, fetch student details if needed
    student = get_object_or_404(QMODEL.Student, id=student_id)

    context = {
        "student": student,
        "results": results,
        "total_results": results.count(),  # Count of results for this student
    }

    return render(request, "teacher/teacher_student_marks.html", context)


@login_required
@user_passes_test(is_teacher)
def chat_view(request, session_id):
    # Fetch the exam session by ID
    exam_session = get_object_or_404(QMODEL.ExamSession, id=session_id)

    # Get the course related to this exam session
    course = exam_session.course

    # Check if the logged-in teacher is the creator of the course
    if request.user != course.creator:
        # Optionally, handle unauthorized access
        return render(
            request, "teacher/unauthorized.html"
        )  # Redirect or show an error message

    if request.method == "POST":
        message_content = request.POST.get("message")

        # Create a new chat message associated with the exam session
        QMODEL.ChatMessage.objects.create(
            session=exam_session,
            sender=request.user,  # The logged-in proctor
            message=message_content,
        )
        return redirect(
            "chat_view", session_id=session_id
        )  # Redirect to see the new message

    context = {
        "exam_session": exam_session,
    }
    return render(request, "teacher/chat_view.html", context)


@login_required
@user_passes_test(is_teacher)
def course_sessions_view(request, course_id):
    course = get_object_or_404(QMODEL.Course, id=course_id)
    active_sessions = QMODEL.ExamSession.objects.filter(course=course, is_active=True)

    context = {
        "course": course,
        "active_sessions": active_sessions,
    }
    return render(request, "teacher/course_sessions_view.html", context)


@login_required
@user_passes_test(is_teacher)
def send_message(request, session_id):
    exam_session = get_object_or_404(QMODEL.ExamSession, id=session_id)

    if request.method == "POST":
        message_content = request.POST.get("message")
        QMODEL.ChatMessage.objects.create(
            session=exam_session,
            sender=request.user,  # Assuming the logged-in user is the sender
            message=message_content,
        )
        return redirect(
            "chat_view", session_id=session_id
        )  # Redirect back to the chat view

    return redirect("chat_view", session_id=session_id)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User
import random




def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        # Check if the email exists in the user database
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email address not found in our records.")
            return render(request, 'teacher/forgot_password.html')
        
        # Generate a 6-digit OTP
        otp = random.randint(100000, 999999)
        
        # Store OTP and email in the session for later verification
        request.session['otp'] = otp
        request.session['email'] = email
        
        # Send OTP via email
        subject = "Reset Your Password - TestMate"
        message = (
            f"Dear {user.first_name},\n\n"  # Use the username from the user object
            "We received a request to reset your password for your TestMate account. "
            "Please use the One-Time Password (OTP) below to proceed with resetting your password:\n\n"
            f"Your OTP: {otp}\n\n"
            "If you did not request a password reset, please ignore this email or contact support immediately.\n\n"
            "Thank you,\n"
            "Team TestMate"
        )
        from_email = 'noinfo.testmate@gmail.com'  # Your sender email
        recipient_list = [email]
        
        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
            )
            messages.success(request, "An OTP has been sent to your email. Please check your inbox.")
            return redirect('verify_otp')  # Redirect to OTP verification page
        except Exception as e:
            # Handle potential email sending failure
            messages.error(request, f"Failed to send OTP. Please try again later. Error: {str(e)}")
    
    return render(request, 'teacher/forgot_password.html')

def verify_otp(request):
    if request.method == "POST":
        otp = "".join([
            request.POST.get(f"otp_{i}") for i in range(1, 7)
        ])  # Concatenate inputs
        if otp.isdigit() and int(otp) == request.session.get('otp'):
            messages.success(request, "OTP verified! You can now reset your password.")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'teacher/verify_otp.html')


from django.contrib.auth.models import User

def reset_password(request):
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            email = request.session.get('email')
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            return redirect('teacherlogin')  # Adjust as per your login page URL
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'teacher/reset_password.html')

