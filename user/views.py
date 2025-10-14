from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import OneTimeCode
from .serializers import (
    RegisterSerializer, UserPublicSerializer, ProfileSerializer, UserSerializer,
    ActivationSendSerializer, ActivationVerifySerializer,
    LoginSerializer, LogoutSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
)
from .utils import generate_numeric_code, expiry

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.ACCOUNT_ACTIVATION,
            code=generate_numeric_code(6),
            expires_at=expiry(10),
        )
        send_mail(
            subject='Your activation code',
            message=f'Your code is: {otp.code}',
            from_email=None,
            recipient_list=[user.email],
        )
        return Response({'detail': 'Registered. Check email for activation code.'}, status=status.HTTP_201_CREATED)


class ResendActivationOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ActivationSendSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.ACCOUNT_ACTIVATION,
            code=generate_numeric_code(6),
            expires_at=expiry(10),
        )
        send_mail(
            subject='Your activation code',
            message=f'Your code is: {otp.code}',
            from_email=None,
            recipient_list=[user.email],
        )
        return Response({'detail': 'Activation code sent.'})


class VerifyActivationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ActivationVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']
        otp = ser.validated_data['otp']

        user.is_active = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        return Response({'detail': 'Account activated.'})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserPublicSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = LogoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = RefreshToken(ser.validated_data['refresh'])
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ForgotPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.PASSWORD_RESET,
            code=generate_numeric_code(6),
            expires_at=expiry(10),
        )
        send_mail(
            subject='Your password reset code',
            message=f'Your code is: {otp.code}',
            from_email=None,
            recipient_list=[user.email],
        )
        return Response({'detail': 'Reset code sent if the email exists.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']
        otp = ser.validated_data['otp']
        new_password = ser.validated_data['new_password']

        user.set_password(new_password)
        user.save(update_fields=['password'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        return Response({'detail': 'Password reset successful.'})


class MeView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPublicSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        request_data = request.data.copy()
        profile_data = request_data.pop('profile', {})

        user_ser = UserSerializer(user, data=request_data, partial=True)
        user_ser.is_valid(raise_exception=True)
        user_ser.save()

        prof_ser = ProfileSerializer(user.profile, data=profile_data, partial=True)
        prof_ser.is_valid(raise_exception=True)
        prof_ser.save()
        
        return Response(UserPublicSerializer(user).data)