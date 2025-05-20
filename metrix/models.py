from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question {self.question_id}: {self.text[:50]}"

class Research(models.Model):
    research_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    person_count = models.PositiveIntegerField()
    question_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Owner: {self.owner})"


class ResearchQuestion(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    choice_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('research', 'question')

    def __str__(self):
        return f"Q: {self.question.text} | R: {self.research.name} | Min choices: {self.choice_count}"


class Participant(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE)
    participant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (Research: {self.research.name})"