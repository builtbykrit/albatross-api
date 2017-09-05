from rest_framework import serializers
from .models import Invitation


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ('email',)

    email = serializers.ReadOnlyField(source='to_user_email')

