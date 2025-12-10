from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from companies.models import Company
from django.core.validators import RegexValidator, EmailValidator

User = get_user_model()


class UserSignupSerializer(serializers.ModelSerializer):
    # Company fields
    company_name = serializers.CharField(max_length=255, required=True)
    company_email = serializers.EmailField(validators=[EmailValidator()], required=True)
    phone = serializers.CharField(
        required=True,
        validators=[RegexValidator(regex=r'^\+?\d{7,15}$', message="Enter a valid phone number.")]
    )
    website = serializers.CharField(
        required=True,
        validators=[RegexValidator(
            regex=r'^www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}$',
            message="Website must be in format www.example.com"
        )]
    )
    description = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.IntegerField(required=True)
    street_address = serializers.CharField(required=True)
    industry = serializers.CharField(required=True)
    company_size = serializers.CharField(required=True)
    company_since = serializers.IntegerField(required=True)
    company_logo = serializers.ImageField(required=False, allow_null=True)

    # User fields
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'password', 'confirm_password',
            'company_name', 'company_email', 'phone', 'website', 'description',
            'country', 'city', 'postal_code', 'street_address', 'industry',
            'company_size', 'company_since', 'company_logo'
        ]

    def validate(self, attrs):
        # Confirm password match
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Extract address components
        street = validated_data.pop('street_address')
        city = validated_data.pop('city')
        country = validated_data.pop('country')
        postal_code = validated_data.pop('postal_code')
        full_address = f"{street}, {city}, {country} - {postal_code}"

        # Extract company data
        company_data = {
            'name': validated_data.pop('company_name'),
            'email': validated_data.pop('company_email'),
            'phone': validated_data.pop('phone'),
            'website': validated_data.pop('website'),
            'description': validated_data.pop('description'),
            'industry': validated_data.pop('industry'),
            'company_size': validated_data.pop('company_size'),
            'company_since': validated_data.pop('company_since'),
            'status': 'pending',
            'company_logo': validated_data.pop('company_logo', None),
            'address': full_address
        }

        # Remove confirm_password
        validated_data.pop('confirm_password')

        # Use company_email as the user's email
        user = User.objects.create_user(
            username=validated_data['username'],
            email=company_data['email'],  # 👈 user.email = company_email
            password=validated_data['password'],
            is_company=True
        )

        # Create company instance
        Company.objects.create(user=user, **company_data)

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    captcha_token = serializers.CharField(write_only=True)  # 🔹 New


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
