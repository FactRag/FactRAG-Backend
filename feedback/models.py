# feedback/models.py
from django.db import models
from django.conf import settings

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('agree', 'Agree'),
        ('disagree', 'Disagree'),
        ('uncertain', 'Uncertain'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    search_term = models.CharField(max_length=255)
    dataset = models.CharField(max_length=100)
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPES,
        default='uncertain'
    )
    comment = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['search_term', 'dataset']),
            models.Index(fields=['user', 'search_term', 'dataset']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s feedback on {self.search_term}"

class FeedbackVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedback_votes'
    )
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    is_upvote = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'feedback')

    def __str__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"{self.user.username}'s {vote_type} on {self.feedback}"