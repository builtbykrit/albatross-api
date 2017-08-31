from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from .models import Membership, Team


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

    class Meta:
        model = Membership
        fields = ('created_at', 'id', 'role', 'state', 'user')

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
        fields = ('created_at', 'id', 'memberships', 'name')

    class JSONAPIMeta:
        included_resources = ['memberships']

    def create(self, validated_data):
        team = Team(creator=validated_data['user'],
                    name=validated_data['name'])
        team.save()
        return team
