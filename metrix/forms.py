from django import  forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Question, Research, Participant, ResearchQuestion

from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class CustomUserAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']


class AddQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'maxlength': '255',  # frontend validation
                'rows': 1,
                'placeholder': 'Enter question text (max 255 chars)',
            }),
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) > 255:
            raise forms.ValidationError("Question text cannot exceed 255 characters.")
        return text

class ResearchCreateForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = ['name', 'person_count','question_count']

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'age', 'gender', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,  # wysokość w linijkach
                'style': 'resize:vertical; max-height:150px;'
            }),
        }

class ResearchQuestionForm(forms.Form):
    question = forms.ModelChoiceField(queryset=Question.objects.all())
    choice_count = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        max_choices = kwargs.pop('max_choices', None)
        super().__init__(*args, **kwargs)
        if max_choices is not None:
            self.fields['choice_count'].max_value = max_choices
            self.fields['choice_count'].widget.attrs['max'] = max_choices

