from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('list/', views.get_feedback_list, name='get_feedback_list'),
    path('stats/', views.get_feedback_stats, name='get_feedback_stats'),
    path('vote/', views.vote_feedback, name='vote_feedback'),
]