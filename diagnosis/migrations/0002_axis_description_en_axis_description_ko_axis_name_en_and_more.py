# Generated by Django 5.0.13 on 2025-06-23 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='axis',
            name='description_en',
            field=models.TextField(blank=True, help_text='Optional description for the axis.', null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='description_ko',
            field=models.TextField(blank=True, help_text='Optional description for the axis.', null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='name_en',
            field=models.CharField(help_text="Full name of the axis (e.g., 'Planning vs Improvising').", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='name_ko',
            field=models.CharField(help_text="Full name of the axis (e.g., 'Planning vs Improvising').", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_communication_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_communication_ko',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_condition_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_condition_ko',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_develop_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_develop_ko',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_style_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='axis',
            name='work_style_ko',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='option_a_en',
            field=models.CharField(help_text='Text for option A.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='option_a_ko',
            field=models.CharField(help_text='Text for option A.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='option_b_en',
            field=models.CharField(help_text='Text for option B.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='option_b_ko',
            field=models.CharField(help_text='Text for option B.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='text_en',
            field=models.CharField(help_text='The text of the question.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='text_ko',
            field=models.CharField(help_text='The text of the question.', max_length=255, null=True),
        ),
    ]
