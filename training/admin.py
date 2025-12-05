# training/admin.py
from django.contrib import admin
from .models import Course, Question, UserAttempt

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_recurring')
    list_filter = ('is_recurring', 'required_for_groups')
    inlines = [QuestionInline]
    search_fields = ('title',)

@admin.register(UserAttempt)
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'is_passed', 'score', 'date_completed')
    list_filter = ('is_passed', 'course')
    date_hierarchy = 'date_completed'
    search_fields = ('user__username', 'course__title')
    
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # This registration is usually optional if you use the inline, but ensures full access
    list_display = ('text', 'course', 'correct_answer')
    list_filter = ('course',)