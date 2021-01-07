from rest_framework import serializers
from core.models import Tag


class TagSerilizer(serializers.ModelSerializer):
    """Serializer for Tag object"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id', )