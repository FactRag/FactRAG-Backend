from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'search_term', 'dataset', 'feedback_type', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('search_term', 'dataset', 'comment')
    date_hierarchy = 'created_at'
