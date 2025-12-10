from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserSignupSerializer, UserLoginSerializer
from django.contrib.auth import get_user_model
from companies.models import Company
from django.core.mail import send_mail
from django.urls import reverse
import requests
from django.conf import settings
from .serializers import PasswordResetRequestSerializer, PasswordResetSerializer


User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SignupView(generics.CreateAPIView):
    serializer_class = UserSignupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'company_email': user.email,  # 👈 return this instead
            },
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        captcha_token = serializer.validated_data['captcha_token']

        # Step 1: Verify captcha with Google
        captcha_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': captcha_token
            }
        ).json()

        if not captcha_response.get('success'):
            return Response({'error': 'Invalid CAPTCHA. Please try again.'}, status=400)

        # Step 2: Authenticate user
        company_email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            company = Company.objects.get(email=company_email)
            user = company.user
        except Company.DoesNotExist:
            return Response({'error': 'Invalid email or password'}, status=401)

        user = authenticate(request, username=user.username, password=password)
        if not user:
            return Response({'error': 'Invalid email or password'}, status=401)

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'company_email': company.email,
                'company_name': company.name,
            },
            'tokens': tokens
        }, status=200)




class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        token = default_token_generator.make_token(user)

        # Construct reset URL
        reset_url = f"http://localhost:3000/reset-password?token={token}&email={email}"  
        # replace localhost with your frontend domain

        send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,  # ✅ no-reply email
            recipient_list=[email],
        )

        return Response({"message": "Password reset link sent to email."}, status=status.HTTP_200_OK)


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        email = request.data.get('email')
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)