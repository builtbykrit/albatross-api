from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from .models import Category, Item, Project


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'description', 'estimated', 'category', 'actual', 'created_at', 'updated_at')


class CategorySerializer(serializers.ModelSerializer):
    included_serializers = {
        'items': ItemSerializer
    }

    items = ResourceRelatedField(
        queryset=Item.objects,
        many=True,
        default=[]
    )

    class Meta:
        model = Category
        fields = ('id', 'name', 'estimated', 'project', 'items', 'actual', 'created_at', 'updated_at')

    class JSONAPIMeta:
        included_resources = ['items']


class ProjectSerializer(serializers.ModelSerializer):
    included_serializers = {
        'categories': CategorySerializer
    }

    categories = ResourceRelatedField(
            queryset=Category.objects,
            many=True,
            default=[]
    )

    class Meta:
        model = Project
        fields = ('id', 'name', 'estimated', 'categories', 'actual', 'created_at', 'updated_at')

    class JSONAPIMeta:
        included_resources = ['categories']
