from .models import CustomUserManager
from django.http import JsonResponse
from django.shortcuts import redirect
from .exceptions import *


def auth_required(func):
    '''
    Decorator to ensure that the user is logged in or not
    :param func:
    :return: Calling required function, if it satisfies 3 condition mentioned in code, otherwise redirecting to the login page
    '''
    def new_func(*args, **kwargs):
        if args:
                request = args[0]
        else:
                request = kwargs['request']
        try:
            auth_token = None
            if 'web' in request.path:
                auth_token = request.session.get('x-inv-auth-token', None)
            else:
                if 'x-inv-auth-token' in request.headers and request.headers['x-inv-auth-token']:
                    auth_token = request.headers['x-inv-auth-token']
            if not auth_token:
                    raise InvalidCredentialsException
            user = CustomUserManager.get_user(auth_token=auth_token)
            if user and CustomUserManager.is_authenticated(user=user):
                kwargs['user'] = user
                return func(*args, **kwargs)
            else:
                raise InvalidCredentialsException
        except InvalidCredentialsException:
            if 'web' in request.path:
                return redirect('login')
            else:
                return JsonResponse(data={"Error": "Unauthorized Request"}, status=401)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    return new_func
