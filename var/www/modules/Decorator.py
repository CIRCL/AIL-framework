#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from flask import request

def login_required(role="ANY"):
    @wraps(role)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        elif (not current_user.is_in_role(role)) and (role != "ANY"):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view
