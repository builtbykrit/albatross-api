from django.contrib.auth.models import User
from django.contrib.auth.password_validation import \
    validate_password as _validate_password
from rest_framework_json_api import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('date_joined', 'email', 'first_name', 'is_staff',
                  'is_superuser', 'is_active', 'last_name',
                  'password')
        read_only_fields = ('is_staff', 'is_superuser', 'is_active', 'date_joined',)
        write_only_fields = ('password',)

    def create(self, validated_data):
        user = User(email=validated_data['email'],
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                    username=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_password(self, password):
        _validate_password(password)
        return password