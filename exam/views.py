from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import spacy
from spellchecker import SpellChecker
import Levenshtein
from nltk.corpus import words





# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# Initialize the spell checker
spell = SpellChecker()

eng = words.words()




def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'exam/index.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
                
    elif is_teacher(request.user):
        accountapproval=TMODEL.Teacher.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')
        else:
            return render(request,'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'total_course':models.Course.objects.all().count(),
    'total_question':models.Question.objects.all().count(),
    }
    return render(request,'exam/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict={
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'pending_teacher':TMODEL.Teacher.objects.all().filter(status=False).count(),
    'salary':TMODEL.Teacher.objects.all().filter(status=True).aggregate(Sum('salary'))['salary__sum'],
    }
    return render(request,'exam/admin_teacher.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'exam/admin_view_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def update_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=TMODEL.User.objects.get(id=teacher.user_id)
    userForm=TFORM.TeacherUserForm(instance=user)
    teacherForm=TFORM.TeacherForm(request.FILES,instance=teacher)
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=TFORM.TeacherUserForm(request.POST,instance=user)
        teacherForm=TFORM.TeacherForm(request.POST,request.FILES,instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request,'exam/update_teacher.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')




@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=False)
    return render(request,'exam/admin_view_pending_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def approve_teacher_view(request,pk):
    teacherSalary=forms.TeacherSalaryForm()
    if request.method=='POST':
        teacherSalary=forms.TeacherSalaryForm(request.POST)
        if teacherSalary.is_valid():
            teacher=TMODEL.Teacher.objects.get(id=pk)
            teacher.salary=teacherSalary.cleaned_data['salary']
            teacher.status=True
            teacher.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-pending-teacher')
    return render(request,'exam/salary_form.html',{'teacherSalary':teacherSalary})

@login_required(login_url='adminlogin')
def reject_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-pending-teacher')

@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'exam/admin_view_teacher_salary.html',{'teachers':teachers})




@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    }
    return render(request,'exam/admin_student.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'exam/admin_view_student.html',{'students':students})



@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    userForm=SFORM.StudentUserForm(instance=user)
    studentForm=SFORM.StudentForm(request.FILES,instance=student)
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=SFORM.StudentUserForm(request.POST,instance=user)
        studentForm=SFORM.StudentForm(request.POST,request.FILES,instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')
    return render(request,'exam/update_student.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'exam/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'exam/admin_add_course.html',{'courseForm':courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request,'exam/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')



@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'exam/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm=forms.QuestionForm()
    if request.method=='POST':
        questionForm=forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question=questionForm.save(commit=False)
            course=models.Course.objects.get(id=request.POST.get('courseID'))
            question.course=course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-question')
    return render(request,'exam/admin_add_question.html',{'questionForm':questionForm})


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'exam/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'exam/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'exam/admin_view_student_marks.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_marks_view(request,pk):
    courses = models.Course.objects.all()
    response =  render(request,'exam/admin_view_marks.html',{'courses':courses})
    response.set_cookie('student_id',str(pk))
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student= SMODEL.Student.objects.get(id=student_id)

    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'exam/admin_check_marks.html',{'results':results})
    




def aboutus_view(request):
    return render(request,'exam/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'exam/contactussuccess.html')
    return render(request, 'exam/contactus.html', {'form':sub})






# Correct spelling before processing the message
def correct_spelling(user_input):
    # Split the input into words
    words = user_input.split()
    # Correct each word; if correction returns None, keep the original word
    corrected_words = [spell.correction(word) if spell.correction(word) else word for word in words]
    # Join the corrected words back into a single string
    return ' '.join(corrected_words)

# Find the closest match to the word from a list using Levenshtein distance
def find_closest_match(word, word_list):
    # Calculate distances between the input word and each word in the list
    distances = {w: Levenshtein.distance(word, w) for w in word_list}
    # Find the word with the minimum distance
    closest_word = min(distances, key=distances.get)
    return closest_word

# Determine intent based on the corrected message
def get_intent(message):
    # Correct spelling of the message first
    corrected_message = correct_spelling(message)
    print(f"Corrected Message: {corrected_message}")  # Debug statement

    # Process the corrected message using the NLP model
    doc = nlp(corrected_message.lower())

    # Define a list of known keywords for intent detection
    greetings = ['hello', 'hi', 'hii', 'hey', 'helloo', 'hellooo']

    # Find the closest greeting word
    closest_greeting = find_closest_match(corrected_message, greetings)
    print(f"Closest Greeting: {closest_greeting}")  # Debug statement

    # Check if the corrected message is close to any known greetings
    if Levenshtein.distance(corrected_message, closest_greeting) <= 2:
        return 'greeting'

    # Check for specific keywords and patterns to identify intents
    if any(token.text in greetings for token in doc):
        return 'greeting'
    elif any(token.lemma_ == 'login' for token in doc):
        return 'login_info'
    elif any(ent.label_ == 'DATE' or token.lemma_ in ['exam', 'schedule'] for ent in doc.ents for token in doc):
        return 'exam_schedule'
    elif 'format' in corrected_message and 'exam' in corrected_message:
        return 'exam_format'
    elif 'practice' in corrected_message and 'test' in corrected_message:
        return 'practice_test'
    elif any(token.lemma_ == 'proctor' for token in doc) or 'proctoring' in corrected_message:
        return 'proctoring_info'
    elif any(token.lemma_ in ['technical', 'issue', 'problem'] for token in doc):
        return 'technical_assistance'
    elif 'rule' in corrected_message or 'exam rules' in corrected_message:
        return 'exam_rules'
    elif 'profile' in corrected_message and any(token.lemma_ == 'update' for token in doc):
        return 'profile_management'
    elif any(token.lemma_ in ['result', 'score', 'marks'] for token in doc):
        return 'exam_results'
    elif any(token.lemma_ in ['prepare', 'study', 'tip'] for token in doc):
        return 'exam_preparation'
    elif 'contact' in corrected_message or 'support' in corrected_message:
        return 'contact_support'
    elif 'room' in corrected_message and 'setup' in corrected_message or 'exam environment' in corrected_message:
        return 'exam_environment'
    elif any(token.lemma_ in ['cheat', 'violation', 'dishonest'] for token in doc):
        return 'cheating_info'
    elif any(token.lemma_ in ['eat', 'during', 'exam'] for token in doc):
        return 'eating_during_exam'
    elif any(token.text in ['exit', 'quit', 'goodbye', 'bye'] for token in doc):
        return 'exit'
    else:
        # Default intent if no other intents are matched
        return 'default'

@csrf_exempt
def chatbot_view(request):
    if request.method == 'POST':
        try:
            # Load the user's message from the request body
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            print(f"User Message: {user_message}")  # Debug statement

            # Check if it's the first interaction or if the message is a start/init signal
            if not user_message or user_message in ['start', 'init']:
                response_message = 'Hello! I am Senpai. Welcome to TestMate 🥰! If you need any help, please ask!'
            else:
                # Process the user's query and get the intent
                intent = get_intent(user_message)
                print(f"Detected Intent: {intent}")  # Debug statement

                # Map intents to response messages
                response_map = {
                    'greeting': 'Hello! How can I assist you today?',
                    'login_info': 'To login, please visit the login page and enter your credentials.',
                    'exam_schedule': 'The next exam is scheduled for September 15, 2024.',
                    'exam_format': 'The exam format will include multiple-choice questions.',
                    'practice_test': 'Practice tests are available on the dashboard under the "Practice" section.',
                    'proctoring_info': 'The proctoring system monitors your webcam and screen activity during the exam.',
                    'technical_assistance': 'For technical issues, ensure your webcam and microphone are connected and functioning. Contact support if the issue persists.',
                    'exam_rules': 'Please ensure you are alone in the room, and do not use any unauthorized materials.',
                    'profile_management': 'You can update your profile information from the profile settings page.',
                    'exam_results': 'Exam results will be available on the results page as soon as you finish the exam.',
                    'exam_preparation': 'Check out our study tips section for effective exam preparation strategies.',
                    'contact_support': 'For further assistance, please visit our Contact Us page.',
                    'exam_environment': 'Ensure your room is well-lit and free from disturbances for a smooth exam experience.',
                    'cheating_info': 'Cheating is strictly prohibited and can lead to disqualification from the exam.',
                    'eating_during_exam': 'Eating during the exam is generally not allowed. Please refer to the exam guidelines or contact support for specific rules.',
                    'exit': 'Goodbye! If you need further assistance, feel free to reach out again.',
                    'default': "I'm not sure how to help with that. Please visit our Contact Us page for further assistance."
                }

                # Generate the response message based on the detected intent
                response_message = response_map.get(intent, "I'm not sure how to help with that. Please visit our Contact Us page for further assistance.")
                print(f"Response Message: {response_message}")  # Debug statement

            # Return the response message as JSON
            return JsonResponse({'response': response_message})

        except json.JSONDecodeError:
            # Handle JSON decoding errors
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Handle invalid request methods
    return JsonResponse({'error': 'Invalid request method'}, status=405)