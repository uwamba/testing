from django import forms
from django.contrib import admin
from .models import Question, Quiz, StudentAnswer

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If the question type is already set to 'MC' (Multiple Choice), show max_selection field.
        if self.instance and self.instance.question_type == 'MC':
            self.fields['max_selection'].widget = forms.NumberInput(attrs={'min': 1, 'max': 10})
        else:
            # Hide max_selection field if question type is not MC
           self.fields['max_selection'].widget = forms.NumberInput(attrs={'min': 1, 'max': 1})

    # Update max_selection visibility dynamically based on question_type selection
    def clean(self):
        print("selected option ...................................................................")
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')

        # Show or hide max_selection based on question_type
        if question_type != 'MC':
            cleaned_data['max_selection'] = None

        return cleaned_data

