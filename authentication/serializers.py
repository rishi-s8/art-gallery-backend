from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'organization', 'is_verified', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'organization']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        """Validate that the passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            organization=validated_data.get('organization', '')
        )
        
        # Generate verification token
        user.generate_verification_token()
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that also returns user data."""
    
    def validate(self, attrs):
        """Validate credentials and return tokens plus user data."""
        data = super().validate(attrs)
        
        # Add user data to response
        user = self.user
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'organization': user.organization,
            'is_verified': user.is_verified
        }
        
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for refreshing an authentication token."""
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        """Validate the refresh token and return a new access token."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken(attrs['refresh_token'])
        
        data = {
            'access_token': str(refresh.access_token),
            'token_type': 'bearer',
            'expires_in': api_settings.ACCESS_TOKEN_LIFETIME.total_seconds(),
        }
        
        if api_settings.ROTATE_REFRESH_TOKENS:
            refresh.set_jti()
            refresh.set_exp()
            
            data['refresh_token'] = str(refresh)
        
        return data


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing a user's password."""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate the current password and that the new passwords match."""
        user = self.context['request'].user
        
        # Check current password
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({"current_password": "Wrong password"})
        
        # Check new passwords match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords don't match"})
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate that the new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords don't match"})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    token = serializers.CharField(required=True)


class ApiKeySerializer(serializers.Serializer):
    """Serializer for API key management."""
    api_key = serializers.CharField(read_only=True)