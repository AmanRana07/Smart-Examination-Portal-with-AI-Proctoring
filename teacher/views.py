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


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    dict = {
        "total_course": QMODEL.Course.objects.all().count(),
        "total_question": QMODEL.Question.objects.all().count(),
        "total_student": SMODEL.Student.objects.all().count(),
    }
    return render(request, "teacher/teacher_dashboard.html", context=dict)


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
