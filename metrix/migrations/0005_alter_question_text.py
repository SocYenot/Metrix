# Generated by Django 5.2.1 on 2025-05-21 12:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metrix', '0004_research_question_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(validators=[django.core.validators.MaxLengthValidator(255)]),
        ),
    ]
