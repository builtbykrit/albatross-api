from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from teams.models import Membership, Team
from .models import UserProfile


UserModel = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('created_at', 'id', 'name')


class MembershipSerializer(serializers.ModelSerializer):
    included_serializers = {
        'team': TeamSerializer
    }

    team = ResourceRelatedField(
        queryset=Team.objects
    )

    class Meta:
        model = Membership
        fields = ('created_at', 'id', 'role', 'state', 'team', 'user')

    class JSONAPIMeta:
        included_resources = ['team']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('toggl_api_key',)

class UserSerializer(serializers.ModelSerializer):
    included_serializers = {
        'memberships': MembershipSerializer,
        'profile': ProfileSerializer
    }

    memberships = ResourceRelatedField(
        queryset=UserModel.memberships,
        many=True,
        default=[]
    )

    profile = ResourceRelatedField(
        queryset=UserProfile.objects,
        many=False
    )

    class Meta:
        model = UserModel
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        } # write_only_fields were removed from DRF as of 3.2

    class JSONAPIMeta:
        included_resources = ['memberships', 'profile']