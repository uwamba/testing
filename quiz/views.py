import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Question, StudentAnswer,MultipleChoiceOption
from main.models import Student, Course, Faculty
from main.views import is_faculty_authorised, is_student_authorised
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, F, FloatField, Q, Prefetch
from django.db.models.functions import Cast
import logging

logger = logging.getLogger(__name__)
def quiz(request, code):
    try:
        course = Course.objects.get(code=code)
        if is_faculty_authorised(request, code):
            if request.method == 'POST':
                title = request.POST.get('title')
                description = request.POST.get('description')
                start = request.POST.get('start')
                end = request.POST.get('end')
                publish_status = request.POST.get('checkbox')
                quiz = Quiz(title=title, description=description, start=start,
                            end=end, publish_status=publish_status, course=course)
                quiz.save()
                return redirect('addQuestion', code=code, quiz_id=quiz.id)
            else:
                return render(request, 'quiz/quiz.html', {'course': course, 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id'])})

        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


def addQuestion(request, code, quiz_id):
    try:
        course = Course.objects.get(code=code)
        if is_faculty_authorised(request, code):
            quiz = Quiz.objects.get(id=quiz_id)
            if request.method == 'POST':
                question = request.POST.get('question')
                option1 = request.POST.get('option1')
                option2 = request.POST.get('option2')
                option3 = request.POST.get('option3')
                option4 = request.POST.get('option4')
                answer = request.POST.get('answer')
                marks = request.POST.get('marks')
                explanation = request.POST.get('explanation')
                question = Question(question=question, option1=option1, option2=option2,
                                    option3=option3, option4=option4, answer=answer, quiz=quiz, marks=marks, explanation=explanation)
                question.save()
                messages.success(request, 'Question added successfully')
            else:
                return render(request, 'quiz/addQuestion.html', {'course': course, 'quiz': quiz, 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id'])})
            if 'saveOnly' in request.POST:
                return redirect('allQuizzes', code=code)
            return render(request, 'quiz/addQuestion.html', {'course': course, 'quiz': quiz, 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id'])})
        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


def allQuizzes(request, code):
    if is_faculty_authorised(request, code):
        course = Course.objects.get(code=code)
        quizzes = Quiz.objects.filter(course=course)
        for quiz in quizzes:
            quiz.total_questions = Question.objects.filter(quiz=quiz).count()
            if quiz.start < datetime.datetime.now():
                quiz.started = True
            else:
                quiz.started = False
            quiz.save()
        return render(request, 'quiz/allQuizzes.html', {'course': course, 'quizzes': quizzes, 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id'])})
    else:
        return redirect('std_login')


def myQuizzes(request, code):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        quizzes = Quiz.objects.filter(course=course)
        student = Student.objects.get(student_id=request.session['student_id'])

        # Determine which quizzes are active and which are previous
        active_quizzes = []
        previous_quizzes = []
        for quiz in quizzes:
            if quiz.end < timezone.now() or quiz.studentanswer_set.filter(student=student).exists():
                previous_quizzes.append(quiz)
            else:
                active_quizzes.append(quiz)

        # Add attempted flag to quizzes
        for quiz in quizzes:
            quiz.attempted = quiz.studentanswer_set.filter(
                student=student).exists()

        # Add total marks obtained, percentage, and total questions for previous quizzes
        for quiz in previous_quizzes:
            student_answers = quiz.studentanswer_set.filter(student=student)
            total_marks_obtained = sum([student_answer.marks for student_answer in student_answers])
            total_marks_obtained = round(total_marks_obtained, 1)
            quiz.total_marks_obtained = total_marks_obtained
            quiz.total_marks = sum(
                [question.marks for question in quiz.question_set.all()])
            quiz.percentage = round(
                total_marks_obtained / quiz.total_marks * 100, 2) if quiz.total_marks != 0 else 0
            quiz.total_questions = quiz.question_set.count()

        # Add total questions for active quizzes
        for quiz in active_quizzes:
            quiz.total_questions = quiz.question_set.count()

        return render(request, 'quiz/myQuizzes.html', {
            'course': course,
            'quizzes': quizzes,
            'active_quizzes': active_quizzes,
            'previous_quizzes': previous_quizzes,
            'student': student,
        })
    else:
        return redirect('std_login')


def startQuiz(request, code, quiz_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        quiz = Quiz.objects.get(id=quiz_id)
        questions = Question.objects.filter(quiz=quiz)
        total_questions = questions.count()

        # Calculate total marks
        marks = 0
        for question in questions:
            marks += question.marks
        quiz.total_marks = marks

        # Preparing question data to handle different question types
        question_data = []
        for question in questions:
            if question.question_type == 'MC':  # Multiple Choice (Multiple answers allowed)
                options = MultipleChoiceOption.objects.filter(question=question)
                question_data.append({
                    'question': question,
                    'type': question.question_type,
                    'options': options,
                    'multiple': True,  # Indicating multiple choices allowed
                })
            elif question.question_type == 'SC':  # Single Choice (Only one answer allowed)
                options = MultipleChoiceOption.objects.filter(question=question)
                question_data.append({
                    'question': question,
                    'type': question.question_type,
                    'options': options,
                    'multiple': False,  # Indicating only one choice allowed
                })
            elif question.question_type == 'TF':  # True/False
                question_data.append({
                    'question': question,
                    'type': question.question_type,
                    'options': options,
                    'multiple': False,  # Only one choice allowed
                })
            elif question.question_type == 'FIB':  # Fill in the Blank
                question_data.append({
                    'question': question,
                    'type': question.question_type,
                    'options': options,  # No options for Fill in the Blank
                    'multiple': False,  # Only one input field allowed
                })

        return render(request, 'quiz/portalStdNew.html', {
            'course': course,
            'quiz': quiz,
            'questions': question_data,  # Pass the processed question data
            'total_questions': total_questions,
            'student': Student.objects.get(student_id=request.session['student_id'])
        })
    else:
        return redirect('std_login')


def studentAnswer(request, code, quiz_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        quiz = Quiz.objects.get(id=quiz_id)
        student = Student.objects.get(student_id=request.session['student_id'])
        questions = Question.objects.filter(quiz=quiz)
        student_answers = StudentAnswer.objects.filter(student=student, quiz=quiz)
        total_marks_obtained = 0
        total_possible_marks = 0

        result_details = []  # To store details for each question

        for question in questions:
         # Retrieve all selected answers for the question
          selected_answers = request.POST.getlist(str(question.id))  # Get multiple answers as a list
          selected_answers_count = len(selected_answers)
          marks=0
          for answer in selected_answers:  # Loop through each selected answer
              answers=MultipleChoiceOption.objects.filter(question=question,is_correct=True)
              answers_count=MultipleChoiceOption.objects.filter(question=question,is_correct=True).count()
              count=0
              for option in answers:  # Loop through all the correct options
                if option.option_text == answer:  # Compare the text of the option with the student's answer
                    print(f"answer true_____________________ {answer}, {option.option_text}")
                    count += 1
                else:
                    print(f"answer false_____________________ {answer}, {option.option_text}")

              print(f"answers_count___________________ {answers_count}")
              if count>answers_count:
                 marks=0
              else:
                 marks=count * question.marks/answers_count
                 
              student_answer = StudentAnswer(
                    student=student,
                    quiz=quiz,
                    question=question,
                    answer=answer,
                    marks=marks
                )
              try:
                student_answer.save()  # Save each selected answer
                print(f"Saved answer for question {question.id}: {answer}")
              except Exception as e:
                    logger.error(f"Error saving answer for Question {question.id}: {str(e)}")
                    redirect('myQuizzes', code=code)

        return redirect('myQuizzes', code=code)  
    
    else:
        return redirect('std_login')


def quizResult(request, code, quiz_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        quiz = Quiz.objects.get(id=quiz_id)
        questions = Question.objects.filter(quiz=quiz)

        try:
            student = Student.objects.get(student_id=request.session['student_id'])
            student_answers = StudentAnswer.objects.filter(student=student, quiz=quiz)

            total_marks_obtained = 0
            for question in questions:
                # Get the student's answers for this question
                student_answers_for_question = student_answers.filter(question=question)
                correct_answers = question.options.filter(is_correct=True)  # Get correct options

                # Check if all the correct answers are selected
                correct_answer_ids = set(correct_answers.values_list('id', flat=True))
                student_answer_ids = set(student_answers_for_question.values_list('answer', flat=True))
                    
                # Calculate marks
                if correct_answer_ids == student_answer_ids:  # Full marks if all correct answers are selected
                    total_marks_obtained += question.marks
                else:  # No partial marking (can adjust based on requirements)
                    pass

            # Set total marks and calculate percentage
            quiz.total_marks_obtained = total_marks_obtained
            quiz.total_marks = sum(question.marks for question in questions)
            quiz.percentage = round((total_marks_obtained / quiz.total_marks) * 100, 2) if quiz.total_marks > 0 else 0

        except Exception as e:
            # Handle errors gracefully
            logger.error(f"Error calculating results: {e}")
            quiz.total_marks_obtained = 0
            quiz.total_marks = 0
            quiz.percentage = 0

        # Add additional details to the questions for rendering
        for question in questions:
            student_answers_for_question = student_answers.filter(question=question)
            question.student_answers = student_answers_for_question  # Store student answers for rendering

        # Calculate time taken for submission
        first_answer = student_answers.order_by('created_at').first()
        last_answer = student_answers.order_by('created_at').last()
        if first_answer and last_answer:
            quiz.time_taken = (last_answer.created_at - quiz.start).total_seconds()
            quiz.time_taken = round(quiz.time_taken, 2)
            quiz.submission_time = last_answer.created_at.strftime("%a, %d-%b-%y at %I:%M %p")
        else:
            quiz.time_taken = 0
            quiz.submission_time = "N/A"

        return render(request, 'quiz/quizResult.html', {
            'course': course,
            'quiz': quiz,
            'questions': questions,
            'student': student
        })
    else:
        return redirect('std_login')



def quizSummary(request, code, quiz_id):
    if is_faculty_authorised(request, code):
        course = Course.objects.get(code=code)
        quiz = Quiz.objects.get(id=quiz_id)

        questions = Question.objects.filter(quiz=quiz)
        time = datetime.datetime.now()
        total_students = Student.objects.filter(course=course).count()
        for question in questions:
            question.A = StudentAnswer.objects.filter(
                question=question, answer='A').count()
            question.B = StudentAnswer.objects.filter(
                question=question, answer='B').count()
            question.C = StudentAnswer.objects.filter(
                question=question, answer='C').count()
            question.D = StudentAnswer.objects.filter(
                question=question, answer='D').count()
        # students who have attempted the quiz and their marks
        students = Student.objects.filter(course=course)
        for student in students:
            student_answers = StudentAnswer.objects.filter(
                student=student, quiz=quiz)
            total_marks_obtained = 0
            for student_answer in student_answers:
                total_marks_obtained += student_answer.question.marks if student_answer.answer == student_answer.question.answer else 0
            student.total_marks_obtained = total_marks_obtained

        if request.method == 'POST':
            quiz.publish_status = True
            quiz.save()
            return redirect('quizSummary', code=code, quiz_id=quiz.id)
        # check if student has attempted the quiz
        for student in students:
            if StudentAnswer.objects.filter(student=student, quiz=quiz).count() > 0:
                student.attempted = True
            else:
                student.attempted = False
        for student in students:
            student_answers = StudentAnswer.objects.filter(
                student=student, quiz=quiz)
            for student_answer in student_answers:
                student.submission_time = student_answer.created_at.strftime(
                    "%a, %d-%b-%y at %I:%M %p")

        context = {'course': course, 'quiz': quiz, 'questions': questions, 'time': time, 'total_students': total_students,
                   'students': students, 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id'])}
        return render(request, 'quiz/quizSummaryFaculty.html', context)

    else:
        return redirect('std_login')


