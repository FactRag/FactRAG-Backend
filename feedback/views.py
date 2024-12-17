# feedback/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import Feedback, FeedbackVote
from .serializers import FeedbackSerializer, FeedbackCreateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    try:
        data = {
            # 'user': request.user.id,
            'search_term': request.data.get('searchTerm'),
            'dataset': request.data.get('dataset'),
            'feedback_type': request.data.get('feedback'),
            'comment': request.data.get('comment', ''),
            'is_public': request.data.get('isPublic', True)
        }

        # Check if user already submitted feedback for this search
        existing_feedback = Feedback.objects.filter(
            user=request.user,
            search_term=data['search_term'],
            dataset=data['dataset']
        ).first()

        if existing_feedback:
            serializer = FeedbackCreateSerializer(
                existing_feedback,
                data=data,
                partial=True
            )
        else:
            serializer = FeedbackCreateSerializer(data=data)

        if serializer.is_valid():
            feedback = serializer.save(user=request.user)
            return Response(
                FeedbackSerializer(feedback, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Error in submit_feedback: {str(e)}")  # Debug print
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([])
def get_feedback_list(request):
    search_term = request.query_params.get('search')
    dataset = request.query_params.get('dataset')

    if not search_term or not dataset:
        return Response(
            {'error': 'Missing search term or dataset'},
            status=status.HTTP_400_BAD_REQUEST
        )

    feedbacks = Feedback.objects.filter(
        search_term=search_term,
        dataset=dataset,
        is_public=True
    ).order_by('-created_at')

    serializer = FeedbackSerializer(
        feedbacks,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([])
def get_feedback_stats(request):
    search_term = request.query_params.get('search')
    dataset = request.query_params.get('dataset')

    if not search_term or not dataset:
        return Response(
            {'error': 'Missing search term or dataset'},
            status=status.HTTP_400_BAD_REQUEST
        )

    stats = Feedback.objects.filter(
        search_term=search_term,
        dataset=dataset
    ).values('feedback_type').annotate(
        count=Count('id')
    )

    result = {
        'agree': 0,
        'disagree': 0,
        'uncertain': 0,
        'total': 0
    }

    for item in stats:
        result[item['feedback_type']] = item['count']
        result['total'] += item['count']

    return Response(result)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_feedback(request):
    try:
        feedback_id = request.data.get('feedbackId')
        is_upvote = request.data.get('isUpvote')

        feedback = Feedback.objects.get(id=feedback_id)

        # Check if user already voted
        existing_vote = FeedbackVote.objects.filter(
            user=request.user,
            feedback=feedback
        ).first()

        if existing_vote:
            if existing_vote.is_upvote == is_upvote:
                # Remove vote if clicking same button
                existing_vote.delete()
            else:
                # Change vote type if clicking different button
                existing_vote.is_upvote = is_upvote
                existing_vote.save()
        else:
            # Create new vote
            FeedbackVote.objects.create(
                user=request.user,
                feedback=feedback,
                is_upvote=is_upvote
            )

        # Return updated feedback
        serializer = FeedbackSerializer(
            feedback,
            context={'request': request}
        )
        return Response(serializer.data)

    except Feedback.DoesNotExist:
        return Response(
            {'error': 'Feedback not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )