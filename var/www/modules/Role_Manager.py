#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from functools import wraps
from flask_login import LoginManager, current_user, logout_user, login_required

from flask import make_response, current_app

login_manager = LoginManager()
login_manager.login_view = 'root.role'

###############################################################
###############          FLASK CACHE         ##################
###############################################################
def no_cache(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    return decorated_view
###############################################################
###############################################################
###############################################################

###############################################################
###############       CHECK ROLE ACCESS      ##################
###############################################################

def login_admin(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_in_role('admin'):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_org_admin(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_in_role('org_admin'):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_user(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_in_role('user'):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_user_no_api(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_in_role('user_no_api'):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_read_only(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_in_role('read_only'):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

###############################################################
###############################################################
