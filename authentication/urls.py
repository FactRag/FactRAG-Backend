from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('orcid/login/', views.orcid_login, name='orcid_login'),
    path('orcid/callback/', views.orcid_callback, name='orcid_callback'),
]