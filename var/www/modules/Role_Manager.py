#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from flask import request, current_app

login_manager = LoginManager()
login_manager.login_view = 'role'

def login_admin(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('admin')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_analyst(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('analyst')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view
