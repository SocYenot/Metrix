from django import  forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Question, Research, Participant, CustomUser, ResearchQuestion

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class CustomUserAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']

class EmailUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text='New email address')

    class Meta:
        model = CustomUser
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class UsernameUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, help_text='New username')

    class Meta:
        model = CustomUser
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class PasswordUpdateForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, label=_("New password"), help_text="Set new password")
    password2 = forms.CharField(widget=forms.PasswordInput, label=_("Confirm password"), help_text="Repeat new password")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data


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


class ConductTestForm(forms.Form):
    def __init__(self, *args, participant=None, questions=None, choices_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            field_name = f"question_{question.id}"
            self.fields[field_name] = forms.ModelMultipleChoiceField(
                label=question.question.text,
                queryset=choices_queryset.exclude(pk=participant.pk),  # <- tu zmiana
                widget=forms.CheckboxSelectMultiple,
                required=True
            )
            self.fields[field_name].max_choices = question.choice_count


    def clean(self):
        cleaned_data = super().clean()
        for name, field in self.fields.items():
            if hasattr(field, 'max_choices'):
                selected = cleaned_data.get(name, [])
                if len(selected) > field.max_choices:
                    self.add_error(name, f"You can select up to {field.max_choices} options.")
        return cleaned_data
