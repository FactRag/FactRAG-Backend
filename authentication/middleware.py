# authentication/middleware.py
from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.middleware import get_user

def jwt_auth_middleware(get_response):
    def middleware(request):
        request.user = SimpleLazyObject(lambda: get_user_from_token(request))
        return get_response(request)

    return middleware

def get_user_from_token(request):
    user = get_user(request)
    if user.is_authenticated:
        return user

    jwt_auth = JWTAuthentication()
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            validated_token = jwt_auth.get_validated_token(auth_header.split(' ')[1])
            user = jwt_auth.get_user(validated_token)
            if user:
                return user
    except:
        pass

    return user