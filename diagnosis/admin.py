from django.contrib import admin
from .models import Axis, Question, Result

# Axis ModelAdmin
class AxisAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')

# Question ModelAdmin
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'option_a', 'option_b')


# Result ModelAdmin
class ResultAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'final_type_axis', 'created_at') # Changed final_type to final_type_axis
    list_filter = ('final_type_axis', 'created_at') # Update filter as well
    search_fields = ('user_email',)


# Register your models here with their ModelAdmin classes
admin.site.register(Axis, AxisAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Result, ResultAdmin)