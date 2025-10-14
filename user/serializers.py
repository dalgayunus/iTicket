from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Profile, OneTimeCode

User = get_user_model()
 
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'avatar', 'date_of_birth', 'country', 'city',
            'address_line1', 'address_line2', 'postal_code',
            'company_name', 'bio',
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'role', 'first_name', 'last_name',
            'is_active', 'email_verified', 'phone_verified', 'profile'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', "first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'role']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.is_active = False
        user.save()
        user.set_password(password)
        user.save(update_fields=['password'])
        return user


class ActivationSendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account with this email.'})
        attrs['user'] = user
        return attrs


class ActivationVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email, code = attrs['email'], attrs['code']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account with this email.'})

        otp_qs = OneTimeCode.objects.filter(
            user=user,
            purpose=OneTimeCode.Purpose.ACCOUNT_ACTIVATION,
            is_used=False,
        ).order_by('-created_at')

        if not otp_qs.exists():
            raise serializers.ValidationError({'code': 'No active code. Request a new one.'})

        otp = otp_qs.first()
        if otp.is_expired():
            raise serializers.ValidationError({'code': 'Code expired. Request a new one.'})
        if otp.code != code:
            raise serializers.ValidationError({'code': 'Invalid code.'})

        attrs['user'] = user
        attrs['otp'] = otp
        return attrs


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs['login']
        password = attrs['password']
        try:
            if '@' in login:
                user = User.objects.get(email=login)
            else:
                user = User.objects.get(username=login)
        except User.DoesNotExist:
            raise serializers.ValidationError({'login': 'Invalid credentials.'})

        if not user.check_password(password):
            raise serializers.ValidationError({'login': 'Invalid credentials.'})

        if not user.is_active:
            raise serializers.ValidationError({'non_field_errors': ['Account not active. Verify your email.']})

        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account with this email.'})
        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=12)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        email, code = attrs['email'], attrs['code']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account with this email.'})

        otp_qs = OneTimeCode.objects.filter(
            user=user,
            purpose=OneTimeCode.Purpose.PASSWORD_RESET,
            is_used=False,
        ).order_by('-created_at')

        if not otp_qs.exists():
            raise serializers.ValidationError({'code': 'No active code. Request a new one.'})

        otp = otp_qs.first()
        if otp.is_expired():
            raise serializers.ValidationError({'code': 'Code expired. Request a new one.'})
        if otp.code != code:
            raise serializers.ValidationError({'code': 'Invalid code.'})

        attrs['user'] = user
        attrs['otp'] = otp
        return attrs