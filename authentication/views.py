from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, views, generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    TokenRefreshSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    ApiKeySerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with the provided details",
        responses={201: UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email (task would be implemented elsewhere)
        from django.core.mail import send_mail
        from django.conf import settings

        # This is a placeholder for the actual email sending logic
        # In a real implementation, this would likely be a Celery task
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.verification_token}"
        send_mail(
            subject="Verify your email address",
            message=f"Please verify your email address by clicking the following link: {verification_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain pair view that also returns user data"""
    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView(views.APIView):
    """Refresh an authentication token"""
    permission_classes = [permissions.AllowAny]
    serializer_class = TokenRefreshSerializer

    @extend_schema(
        summary="Refresh authentication token",
        description="Exchange a refresh token for a new authentication token",
        request=TokenRefreshSerializer,
        responses={200: TokenRefreshSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the current user's information"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(views.APIView):
    """Change the current user's password"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        summary="Change password",
        description="Change the current user's password",
        request=PasswordChangeSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"message": "Password changed successfully"})


class PasswordResetRequestView(views.APIView):
    """Request a password reset"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(
        summary="Request password reset",
        description="Request a password reset email",
        request=PasswordResetRequestSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            user.generate_verification_token()

            # Send password reset email (task would be implemented elsewhere)
            from django.core.mail import send_mail
            from django.conf import settings

            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={user.verification_token}"
            send_mail(
                subject="Reset your password",
                message=f"Please reset your password by clicking the following link: {reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            # Don't reveal whether a user exists
            pass

        return Response({"message": "If the email exists, a password reset link has been sent"})


class PasswordResetConfirmView(views.APIView):
    """Confirm a password reset"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        summary="Confirm password reset",
        description="Reset password using a token",
        request=PasswordResetConfirmSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(verification_token=serializer.validated_data['token'])

            if not user.is_verification_token_valid():
                return Response(
                    {"error": "Token has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.verification_token = None
            user.verification_token_expiry = None
            user.save()

            return Response({"message": "Password reset successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(views.APIView):
    """Verify a user's email address"""
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer

    @extend_schema(
        summary="Verify email",
        description="Verify a user's email address using a token",
        request=EmailVerificationSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(verification_token=serializer.validated_data['token'])

            if not user.is_verification_token_valid():
                return Response(
                    {"error": "Token has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.verify_email()

            return Response({"message": "Email verified successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ApiKeyView(views.APIView):
    """Generate or retrieve an API key for the current user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApiKeySerializer

    @extend_schema(
        summary="Get API key",
        description="Get the current user's API key or generate a new one",
        responses={200: ApiKeySerializer}
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.api_key:
            user.generate_api_key()

        return Response({"api_key": user.api_key})

    @extend_schema(
        summary="Regenerate API key",
        description="Generate a new API key for the current user",
        responses={200: ApiKeySerializer}
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        user.generate_api_key()

        return Response({"api_key": user.api_key})