from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenObtainPairView
from .views import (
    RegisterView, ResendActivationOTPView, VerifyActivationView,
    LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView,
    MeView,
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('activate/send/', ResendActivationOTPView.as_view()),
    path('activate/verify/', VerifyActivationView.as_view()),

    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('token/verify/', TokenVerifyView.as_view()),

    path('password/forgot/', ForgotPasswordView.as_view()),
    path('password/reset/', ResetPasswordView.as_view()),

    path('me/', MeView.as_view()),
]