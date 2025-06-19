from django.contrib import admin
from .models import Axis, Question, Result
from django.http import HttpResponse
import csv
from datetime import datetime

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
    actions = ['delete_empty_email', 'export_all_to_csv']

    def delete_empty_email(self, request, queryset):
        empty_results = Result.objects.filter(user_email__isnull=True) | Result.objects.filter(user_email='')
        count = empty_results.count()
        empty_results.delete()
        self.message_user(request, f"user_email이 비어있는 결과 {count}개가 삭제되었습니다.")
    delete_empty_email.short_description = 'user_email이 비어있는 결과 모두 삭제'

    def export_all_to_csv(self, request, queryset):
        # 전체 Result를 CSV로 내보냄 (선택된 queryset 무시)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"results_all_{today_str}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        # 헤더 작성
        writer.writerow(['id', 'user_email', 'final_type_axis', 'created_at', 'newsletter_consent', 'responses_json', 'scores_json'])
        for result in Result.objects.all():
            writer.writerow([
                result.id,
                result.user_email,
                result.final_type_axis.code if result.final_type_axis else '',
                result.created_at,
                result.newsletter_consent,
                result.responses_json,
                result.scores_json
            ])
        return response
    export_all_to_csv.short_description = '전체 결과를 CSV로 다운로드'


# Register your models here with their ModelAdmin classes
admin.site.register(Axis, AxisAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Result, ResultAdmin)