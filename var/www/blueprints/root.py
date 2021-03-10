#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: root endpoints: login, ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import create_user_db, check_password_strength, check_user_role_integrity
from Role_Manager import login_admin, login_analyst

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
from User import User

r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db
r_serv_tags = Flask_config.r_serv_tags

# ============ BLUEPRINT ============

root = Blueprint('root', __name__, template_folder='templates')

# ============ VARIABLES ============



# ============ FUNCTIONS ============



# ============= ROUTES ==============
@root.route('/login', methods=['POST', 'GET'])
def login():

    current_ip = request.remote_addr
    login_failed_ip = r_cache.get('failed_login_ip:{}'.format(current_ip))

    # brute force by ip
    if login_failed_ip:
        login_failed_ip = int(login_failed_ip)
        if login_failed_ip >= 5:
            error = 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_ip:{}'.format(current_ip)))
            return render_template("login.html", error=error)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        next_page = request.form.get('next_page')

        if username is not None:
            user = User.get(username)
            login_failed_user_id = r_cache.get('failed_login_user_id:{}'.format(username))
            # brute force by user_id
            if login_failed_user_id:
                login_failed_user_id = int(login_failed_user_id)
                if login_failed_user_id >= 5:
                    error = 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_user_id:{}'.format(username)))
                    return render_template("login.html", error=error)

            if user and user.check_password(password):
                if not check_user_role_integrity(user.get_id()):
                    error = 'Incorrect User ACL, Please contact your administrator'
                    return render_template("login.html", error=error)
                login_user(user) ## TODO: use remember me ?
                if user.request_password_change():
                    return redirect(url_for('root.change_password'))
                else:
                    # update note
                    # next page
                    if next_page and next_page!='None' and next_page!='/':
                        return redirect(next_page)
                    # dashboard
                    else:
                        return redirect(url_for('dashboard.index', update_note=True))
            # login failed
            else:
                # set brute force protection
                #logger.warning("Login failed, ip={}, username={}".format(current_ip, username))
                r_cache.incr('failed_login_ip:{}'.format(current_ip))
                r_cache.expire('failed_login_ip:{}'.format(current_ip), 300)
                r_cache.incr('failed_login_user_id:{}'.format(username))
                r_cache.expire('failed_login_user_id:{}'.format(username), 300)
                #

                error = 'Password Incorrect'
                return render_template("login.html", error=error)

        return 'please provide a valid username'

    else:
        next_page = request.args.get('next')
        error = request.args.get('error')
        return render_template("login.html" , next_page=next_page, error=error)

@root.route('/change_password', methods=['POST', 'GET'])
@login_required
def change_password():
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    error = request.args.get('error')

    if error:
        return render_template("change_password.html", error=error)

    if current_user.is_authenticated and password1!=None:
        if password1==password2:
            if check_password_strength(password1):
                user_id = current_user.get_id()
                create_user_db(user_id , password1, update=True)
                # update Note
                # dashboard
                return redirect(url_for('dashboard.index', update_note=True))
            else:
                error = 'Incorrect password'
                return render_template("change_password.html", error=error)
        else:
            error = "Passwords don't match"
            return render_template("change_password.html", error=error)
    else:
        error = 'Please choose a new password'
        return render_template("change_password.html", error=error)

@root.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('root.login'))

# role error template
@root.route('/role', methods=['POST', 'GET'])
@login_required
def role():
    return render_template("error/403.html"), 403

@root.route('/searchbox/')
@login_required
@login_analyst
def searchbox():
    return render_template("searchbox.html")
