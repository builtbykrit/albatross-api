from rest_framework import serializers
from .models import Invitation


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()


class InvitationRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ('email',)

    email = serializers.ReadOnlyField(source='to_user_email')
