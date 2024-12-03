from django.contrib import admin
from .models import Quiz, Question, StudentAnswer, MultipleChoiceOption
from .forms import QuestionForm  # Import the custom form

class MultipleChoiceOptionInline(admin.TabularInline):
    model = MultipleChoiceOption
    extra = 1  # How many empty forms to show by default

class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ('question_text', 'marks', 'quiz','max_selection')
    search_fields = ('question_text',)
    inlines = [MultipleChoiceOptionInline]  # Inline the options for each question


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start', 'end', 'publish_status', 'started')
    list_filter = ('course', 'publish_status', 'started')
    search_fields = ('title',)

class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'question', 'answer', 'marks')
    list_filter = ('quiz', 'question')
    search_fields = ('student__name', 'quiz__title', 'question__question_text')


# Register your models here.
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(StudentAnswer, StudentAnswerAdmin)
admin.site.register(MultipleChoiceOption)  # Register the options model for standalone management
