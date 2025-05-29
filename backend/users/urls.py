from django.urls import path
from .views import CustomUserCreateView, CustomTokenCreateView, CustomTokenDestroyView

urlpatterns = [
    path('users/', CustomUserCreateView.as_view(), name='user-create'),
    path('auth/token/login/', CustomTokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', CustomTokenDestroyView.as_view(), name='token-logout'),
]
