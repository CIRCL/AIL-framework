#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: root endpoints: login, ...
'''

import os
import sys
import time

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask import session
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_analyst

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import Users
from lib.ail_users import AILUser

r_cache = Flask_config.r_cache

# ============ BLUEPRINT ============

root = Blueprint('root', __name__, template_folder='templates')

# ============ VARIABLES ============



# ============ FUNCTIONS ============



# ============= ROUTES ==============
@root.route('/login', methods=['POST', 'GET'])   # TODO LOG BRUTEFORCE ATTEMPT
def login():
    current_ip = request.remote_addr
    login_failed_ip = r_cache.get(f'failed_login_ip:{current_ip}')

    # brute force by IP
    if login_failed_ip:
        login_failed_ip = int(login_failed_ip)
        if login_failed_ip >= 5:
            wait_time = r_cache.ttl(f'failed_login_ip:{current_ip}')
            logging_error = f'Max Connection Attempts reached, Please wait {wait_time}s'
            return render_template("login.html", error=logging_error)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        next_page = request.form.get('next_page')

        if password is None:
            return render_template("login.html", error='Password is required.')

        if username is not None:
            user = AILUser.get(username)  # TODO ANONYMOUS USER

            # brute force by user_id
            login_failed_user_id = r_cache.get(f'failed_login_user_id:{username}')
            if login_failed_user_id:
                login_failed_user_id = int(login_failed_user_id)
                if login_failed_user_id >= 5:
                    wait_time = r_cache.ttl(f'failed_login_user_id:{username}')
                    logging_error = f'Max Connection Attempts reached, Please wait {wait_time}s'
                    return render_template("login.html", error=logging_error)

            if user.exists() and user.check_password(password):
                if not Users.check_user_role_integrity(user.get_user_id()):
                    logging_error = 'Incorrect User ACL, Please contact your administrator'
                    return render_template("login.html", error=logging_error)

                if user.is_2fa_enabled():

                    session['user_id'] = user.get_user_id()
                    session['otp_expire'] = int(time.time()) + 10800

                    if not user.is_2fa_setup():
                        return redirect(url_for('root.setup_2fa'))
                    else:
                        htop_counter = user.get_htop_counter()
                        return redirect(url_for('root.verify_2fa', htop_counter=htop_counter))

                else:
                    # Login User
                    user.rotate_session()
                    login_user(user)

                    if user.request_password_change():
                        return redirect(url_for('root.change_password'))
                    else:
                        # update note
                        # next page
                        if next_page and next_page != 'None' and next_page != '/':
                            return redirect(next_page)
                        # dashboard
                        else:
                            return redirect(url_for('dashboard.index'))

            # LOGIN FAILED
            else:
                # set brute force protection
                # logger.warning("Login failed, ip={}, username={}".format(current_ip, username))
                r_cache.incr(f'failed_login_ip:{current_ip}')
                r_cache.expire(f'failed_login_ip:{current_ip}', 300)
                r_cache.incr(f'failed_login_user_id:{username}')
                r_cache.expire(f'failed_login_user_id:{username}', 300)
                #

                logging_error = 'Login/Password Incorrect'
                return render_template("login.html", error=logging_error)

        return 'Please provide a valid Username'

    else:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        else:
            print(current_user)
            next_page = request.args.get('next')
            error = request.args.get('error')
            return render_template("login.html", next_page=next_page, error=error)

@root.route('/2fa', methods=['POST', 'GET'])  # TODO CHECK IF user_id exists
def verify_2fa():
    user_id = session.get('user_id', None)
    otp_expire = session.get('otp_expire', None)

    if not user_id or not otp_expire:  # TODO LOG
        return redirect(url_for('root.login'))

    # Check if Login is expired
    if otp_expire < int(time.time()):  # TODO LOG
        session.pop('user_id', None)
        session.pop('otp_expire', None)
        error = "First Login Expired"
        return redirect(url_for('root.login', error=error))

    user = AILUser.get(user_id)
    if not user.is_2fa_setup():
        return redirect(url_for('root.setup_2fa'))

    if request.method == 'POST':

        code = request.form.get('otp')

        if user.is_valid_otp(code):
            session.pop('user_id', None)
            session.pop('otp_expire', None)

            # Login User
            user.rotate_session()
            login_user(user)

            if user.request_password_change():
                return redirect(url_for('root.change_password'))
            else:
                # # next page
                # if next_page and next_page != 'None' and next_page != '/':
                #     return redirect(next_page)
                # dashboard
                # else:
                return redirect(url_for('dashboard.index'))
        else:
            htop_counter = user.get_htop_counter()
            error = "The OTP is incorrect or has expired"
            return render_template("verify_otp.html", htop_counter=htop_counter, error=error)

    else:
        htop_counter = user.get_htop_counter()
        return render_template("verify_otp.html", htop_counter=htop_counter)

@root.route('/2fa/setup', methods=['POST', 'GET'])
def setup_2fa():
    user_id = session.get('user_id', None)
    otp_expire = session.get('otp_expire', None)

    if not user_id or not otp_expire:  # TODO LOG
        return redirect(url_for('root.login'))

    # Check if Login is expired
    if otp_expire < int(time.time()):  # TODO LOG
        session.pop('user_id', None)
        session.pop('otp_expire', None)
        error = "First Login Expired"
        return redirect(url_for('root.login', error=error))

    user = AILUser.get(user_id)

    if user.is_2fa_setup():
        return redirect(url_for('root.verify_2fa'))

    if request.method == 'POST':
        code = request.form.get('otp')

        if user.is_valid_otp(code):
            user.setup_2fa()

            session.pop('user_id', None)
            session.pop('otp_expire', None)

            # Login User
            user.rotate_session()
            login_user(user)

            if user.request_password_change():
                return redirect(url_for('root.change_password'))
            else:
                return redirect(url_for('dashboard.index'))
        else:
            error = "The OTP is incorrect or has expired"
            return redirect(url_for('root.setup_2fa', error=error))
    else:
        error = request.args.get('error')
        if error:
            qr_code, hotp_codes = user.init_setup_2fa(create=False)
        else:
            qr_code, hotp_codes = user.init_setup_2fa()
        return render_template("setup_otp.html", qr_code=qr_code, hotp_codes=hotp_codes, error=error)

@root.route('/change_password', methods=['POST', 'GET'])
@login_required
def change_password():
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    error = request.args.get('error')

    if error:
        return render_template("change_password.html", error=error)

    if current_user.is_authenticated and password1 != None:
        if password1 == password2:
            if Users.check_password_strength(password1):
                user_id = current_user.get_user_id()
                Users.create_user(user_id, password=password1, chg_passwd=False)
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
    current_user.kill_session()
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
