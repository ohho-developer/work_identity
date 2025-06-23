from django.db import models
import uuid # Import uuid for the Result model primary key
import json # To store scores and responses as JSON

class Axis(models.Model):
    """Defines a dimension or axis of the personality test (e.g., PI, DN)."""
    code = models.CharField(max_length=4, unique=True, help_text="Short code for the axis (e.g., \'PDCT\').")
    name = models.CharField(max_length=100, help_text="Full name of the axis (e.g., 'Planning vs Improvising').")
    description = models.TextField(blank=True, help_text="Optional description for the axis.")
    work_style = models.TextField(blank=True)
    work_condition = models.TextField(blank=True)
    work_develop = models.TextField(blank=True)
    work_communication = models.TextField(blank=True)
    
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Question(models.Model):
    """Defines a single survey question."""
    # ForeignKey to the Axis model
    text = models.CharField(max_length=255, help_text="The text of the question.")
    option_a = models.CharField(max_length=100, help_text="Text for option A.")
    option_a_value = models.CharField(max_length=1, help_text="Value associated with option A (e.g., 'P').")
    option_b = models.CharField(max_length=100, help_text="Text for option B.")
    option_b_value = models.CharField(max_length=1, help_text="Value associated with option B (e.g., 'I').")

    def __str__(self):
        return f"Q{self.id}: {self.text[:50]}..."

class Result(models.Model):
    """Stores survey results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_email = models.EmailField(blank=True, null=True, help_text="Email address of the user who took the test.")
    responses_json = models.JSONField(help_text="JSON string of raw responses {question_id: value}.")
    scores_json = models.JSONField(null=True, blank=True, help_text="JSON string of calculated axis scores {side_value: score}. e.g., { 'P': 7, 'I': 3, ... }")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the result was created.")
    newsletter_consent = models.BooleanField(default=False, help_text="Indicates if the user consented to receive the newsletter.")
    final_type_axis = models.ForeignKey(Axis, on_delete=models.CASCADE, related_name='results', null=False, help_text="The Axis model representing the final personality type.")

    def __str__(self):
        return f"Result for {self.user_email} ({self.final_type_axis.code})"
 