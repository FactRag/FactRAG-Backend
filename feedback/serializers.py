# feedback/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Feedback, FeedbackVote

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'avatar')

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('search_term', 'dataset', 'feedback_type', 'comment', 'is_public')

class FeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    upvotes = serializers.SerializerMethodField()
    downvotes = serializers.SerializerMethodField()
    has_user_voted = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = (
            'id', 'user', 'search_term', 'dataset', 'feedback_type',
            'comment', 'is_public', 'created_at', 'upvotes', 'downvotes',
            'has_user_voted'
        )
        read_only_fields = ('id', 'user', 'created_at', 'upvotes', 'downvotes', 'has_user_voted')

    def get_upvotes(self, obj):
        return obj.votes.filter(is_upvote=True).count()

    def get_downvotes(self, obj):
        return obj.votes.filter(is_upvote=False).count()

    def get_has_user_voted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        vote = obj.votes.filter(user=request.user).first()
        if not vote:
            return None

        return {
            'upvoted': vote.is_upvote,
            'downvoted': not vote.is_upvote
        }