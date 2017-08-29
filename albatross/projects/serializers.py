from rest_framework import serializers
from .models import Category, Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'categories', 'estimated', 'actual', 'created_at', 'updated_at')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'items', 'estimated', 'actual', 'created_at', 'updated_at')
