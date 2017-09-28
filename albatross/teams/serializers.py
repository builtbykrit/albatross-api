from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from .models import Membership, Team
from invitations.models import Invitation

UserModel = get_user_model()


# Monkey patch the JSONAPIMeta class onto whatever
# UserModel we are using.
class UserJSONAPIMeta:
        resource_name = "users"
UserModel.JSONAPIMeta = UserJSONAPIMeta


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        } # write_only_fields were removed from DRF as of 3.2


class MembershipSerializer(serializers.ModelSerializer):
    included_serializers = {
        'user': UserSerializer
    }

    user = ResourceRelatedField(
        queryset=UserModel.objects
    )

    invitation = ResourceRelatedField(
        queryset=Invitation.objects
    )

    class Meta:
        model = Membership
        fields = ('created_at', 'id', 'role', 'state', 'user', 'invitation')

    class JSONAPIMeta:
        included_resources = ['user']


class TeamSerializer(serializers.ModelSerializer):
    included_serializers = {
        'memberships': MembershipSerializer
    }

    memberships = ResourceRelatedField(
        queryset=Membership.objects,
        many=True,
        default=[]
    )

    class Meta:
        model = Team
        fields = ('created_at', 'id', 'memberships',
                  'name', 'on_trial', 'trial_expires_at',)
        extra_kwargs = {
            'on_trial': {
                'read_only': True,
            },
            'trial_expires_at': {
                'read_only': True,
            },
        }  # write_only_fields were removed from DRF as of 3.2

    class JSONAPIMeta:
        included_resources = ['memberships']

    def create(self, validated_data):
        team = Team(creator=validated_data['user'],
                    name=validated_data['name'])
        team.save()
        return team
