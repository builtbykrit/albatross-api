from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_auth.serializers import PasswordResetSerializer as RestAuthPasswordResetSerializer
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework import serializers as RestSerializer

from teams.models import Membership, Team
from .forms import PasswordResetFrom
from .models import UserProfile

UserModel = get_user_model()


class PasswordResetSerializer(RestAuthPasswordResetSerializer):
    password_reset_form_class = PasswordResetFrom


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
        fields = ('harvest_access_token', 'harvest_refresh_token',
                  'harvest_tokens_last_refreshed_at', 'toggl_api_key',
                  'wants_weekly_emails')

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
        }  # write_only_fields were removed from DRF as of 3.2

    class JSONAPIMeta:
        included_resources = ['memberships', 'profile']

class HarvestSerializer(RestSerializer.Serializer):
    authorization_code = RestSerializer.CharField(required=True, allow_blank=False)