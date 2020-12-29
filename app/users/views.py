from rest_framework import generics

from users.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user"""
    serializer_class = UserSerializer
