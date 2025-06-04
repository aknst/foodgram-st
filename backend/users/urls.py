from django.urls import path
from .views import (
    UserView,
    SingleUserView,
    CustomTokenCreateView,
    CustomTokenDestroyView,
    CurrentUserView,
    PasswordResetView,
    AvatarView,
    SubscriptionView,
    SubscriptionsListView
)

urlpatterns = [
    path("users/", UserView.as_view(), name="user-list"),
    path("users/<int:user_id>/", SingleUserView.as_view(), name="user-detail"),
    path("auth/token/login/", CustomTokenCreateView.as_view(), name="login"),
    path("auth/token/logout/", CustomTokenDestroyView.as_view(), name="logout"),
    path("users/me/", CurrentUserView.as_view(), name="current-user"),
    path("users/set_password/", PasswordResetView.as_view(), name="password-reset"),
    path("users/me/avatar/", AvatarView.as_view(), name="avatar"),
    path("users/<int:user_id>/subscribe/", SubscriptionView.as_view(), name="subscribe"),
    path("users/subscriptions/", SubscriptionsListView.as_view(), name="subscriptions-list"),
]
