from django.urls import path
from .views import UserView, SingleUserView, CustomTokenCreateView, CustomTokenDestroyView, CurrentUserView, AvatarView

urlpatterns = [
    path('users/', UserView.as_view(), name='users'),
    path('users/<int:user_id>/', SingleUserView.as_view(), name='user-detail'),
    path('users/me/', CurrentUserView.as_view(), name='user-me'),
    path('users/me/avatar/', AvatarView.as_view(), name='user-avatar'),
    path('auth/token/login/', CustomTokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', CustomTokenDestroyView.as_view(), name='token-logout'),
]
