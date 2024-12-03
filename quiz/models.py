from django.db import models
from main.models import Student, Course


# Question Types
QUESTION_TYPES = (
    ('MC', 'Multiple Choice'),
    ('SC', 'Single Choice'),
    ('TF', 'True/False'),
    ('FIB', 'Fill in the Blank'),
    # Add other question types as needed
)

class Quiz(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publish_status = models.BooleanField(default=False, null=True, blank=True)
    started = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def duration(self):
        return self.end - self.start
        
    def duration_in_seconds(self):
        return (self.end - self.start).total_seconds()

    def total_questions(self):
        return Question.objects.filter(quiz=self).count()

    def starts(self):
        return self.start.strftime("%a, %d-%b-%y at %I:%M %p")

    def ends(self):
        return self.end.strftime("%a, %d-%b-%y at %I:%M %p")

    def attempted_students(self):
        return Student.objects.filter(studentanswer__quiz=self).distinct().count()


class MultipleChoiceOption(models.Model):
    question = models.ForeignKey('Question', related_name='options', on_delete=models.CASCADE)
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text


class Question(models.Model):
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_text = models.TextField()
    marks = models.IntegerField(default=0)
    explanation = models.TextField(null=True, blank=True)
    
    question_type = models.CharField(
        max_length=3,
        choices=QUESTION_TYPES,
        default='MC',
    )
    max_selection = models.PositiveIntegerField(default=1)  # Limit the number of options a student can select
    
    correct_answer_text = models.TextField(null=True, blank=True)  # For Fill in the Blank and True/False questions

    def __str__(self):
        return self.question_text

    def get_answer(self):
        if self.question_type in ['MC', 'SC']:
            correct_option = self.options.filter(is_correct=True).first()
            return correct_option.option_text if correct_option else None
        elif self.question_type == 'TF':
            return self.correct_answer_text  # For True/False, just return the stored value (True/False)
        elif self.question_type == 'FIB':
            return self.correct_answer_text  # For Fill in the Blank, return the answer text

    def total_correct_answers(self):
        if self.question_type == 'TF':
            # Check if student selected the correct boolean answer for True/False
            return StudentAnswer.objects.filter(question=self, answer__text=self.correct_answer_text).count()
        elif self.question_type == 'FIB':
            # Check if student's answer matches the correct text for Fill in the Blank
            return StudentAnswer.objects.filter(question=self, answer__text=self.correct_answer_text).count()
        else:
            return StudentAnswer.objects.filter(question=self, answer__is_correct=True).count()

    def total_wrong_answers(self):
        if self.question_type == 'TF':
            # Check if student selected the wrong answer for True/False
            return StudentAnswer.objects.filter(question=self).exclude(answer__text=self.correct_answer_text).count()
        elif self.question_type == 'FIB':
            # Check if student's answer does not match the correct answer for Fill in the Blank
            return StudentAnswer.objects.filter(question=self).exclude(answer__text=self.correct_answer_text).count()
        else:
            return StudentAnswer.objects.filter(question=self).exclude(answer__is_correct=True).count()


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(null=True, blank=True)  # For TF and FIB questions, store text answer
    marks = models.DecimalField(
        max_digits=6,    # Maximum number of digits
        decimal_places=5,  # Number of decimal places
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f'{self.student.name} - {self.quiz.title} - {self.question.question_text}'



    
