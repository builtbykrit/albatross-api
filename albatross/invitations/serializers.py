from rest_framework import serializers


class InvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
