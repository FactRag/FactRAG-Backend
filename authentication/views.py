# authentication/views.py
import requests
from jose import jwt
from django.conf import settings
from django.shortcuts import redirect

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from authentication.models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def google_login(request):
    # get the term_id and dataset from the endpoint
    dataset = request.GET.get('dataset')
    term_id = request.GET.get('term_id')

    redirect_uri = 'https://factcheck.dei.unipd.it/api/auth/google/callback'

    return Response({
        'auth_url': f'https://accounts.google.com/o/oauth2/v2/auth?'
                    f'client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}&'
                    f'response_type=code&'
                    f'scope=email profile&'
                    f'redirect_uri={redirect_uri}&'
                    f'state={term_id}_{dataset}'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    term_id, dataset = state.split('_')

    redirect_uri ='https://factcheck.dei.unipd.it/api/auth/google/callback'

    # Exchange code for access token
    token_response = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )

    if not token_response.ok:
        return Response({'error': 'Failed to get token'}, status=status.HTTP_400_BAD_REQUEST)

    # Get user info
    access_token = token_response.json()['access_token']
    user_info = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    # Get or create user
    try:
        user = User.objects.get(email=user_info['email'])
    except User.DoesNotExist:
        user = User.objects.create_user(
            email=user_info['email'],
            username=user_info['email'].split('@')[0],
            provider='google',
            provider_id=user_info['id'],
            avatar=user_info.get('picture', '')
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    tokens = {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

    # Redirect to frontend with tokens
    frontend_url = settings.FRONTEND_URL
    return redirect(f'{frontend_url}/auth/callback?tokens={jwt.encode(tokens, settings.SECRET_KEY)}&dataset={dataset}&term_id={term_id}')

@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_login(request):
    # get the term_id and dataset from the endpoint
    dataset = request.GET.get('dataset')
    term_id = request.GET.get('term_id')

    redirect_uri = 'https://factcheck.dei.unipd.it/api/auth/orcid/callback'
    return Response({
        'auth_url': f'{settings.ORCID_AUTH_URL}?'
                    f'client_id={settings.ORCID_CLIENT_ID}&'
                    f'response_type=code&'
                    f'scope=/authenticate&'
                    f'redirect_uri={redirect_uri}&'
                    f'state={term_id}_{dataset}'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    term_id, dataset = state.split('_')

    redirect_uri = 'https://factcheck.dei.unipd.it/api/auth/orcid/callback'

    # Exchange code for access token
    token_response = requests.post(
        settings.ORCID_TOKEN_URL,
        data={
            'code': code,
            'client_id': settings.ORCID_CLIENT_ID,
            'client_secret': settings.ORCID_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )

    if not token_response.ok:
        return Response({'error': 'Failed to get token'}, status=status.HTTP_400_BAD_REQUEST)

    token_data = token_response.json()
    orcid_id = token_data['orcid']

    # Get ORCID profile
    profile_response = requests.get(
        f'https://pub.orcid.org/v3.0/{orcid_id}/person',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token_data["access_token"]}'
        }
    )

    if not profile_response.ok:
        return Response({'error': 'Failed to get profile'}, status=status.HTTP_400_BAD_REQUEST)

    profile = profile_response.json()

    # Get or create user
    try:
        user = User.objects.get(provider_id=orcid_id)
    except User.DoesNotExist:
        email = profile.get('emails', {}).get('email', [{}])[0].get('email', f'{orcid_id}@orcid.org')
        first_name = profile.get('name', {}).get('given-names', {}).get('value', '')
        last_name = profile.get('name', {}).get('family-name', {}).get('value', '')
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=f'orcid_{orcid_id}',
            provider='orcid',
            provider_id=orcid_id
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    tokens = {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

    # Redirect to frontend with tokens
    frontend_url = settings.FRONTEND_URL
    return redirect(f'{frontend_url}/auth/callback?tokens={jwt.encode(tokens, settings.SECRET_KEY)}&dataset={dataset}&term_id={term_id}')
