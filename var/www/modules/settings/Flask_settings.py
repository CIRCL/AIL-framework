#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the settings modules page
'''
import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for
from flask_login import login_required, current_user

from Role_Manager import login_admin, login_analyst, login_user, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import d4
from lib import Users

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_db = Flask_config.r_serv_db
REPO_ORIGIN = Flask_config.REPO_ORIGIN
dict_update_description = Flask_config.dict_update_description
email_regex = Flask_config.email_regex

settings = Blueprint('settings', __name__, template_folder='templates')


# ============ FUNCTIONS ============

def check_email(email):
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False


# ============= ROUTES ==============

@settings.route("/settings/edit_profile", methods=['GET'])
@login_required
@login_read_only
def edit_profile():
    user_metadata = Users.get_user_metadata(current_user.get_id())
    admin_level = current_user.is_in_role('admin')
    return render_template("edit_profile.html", user_metadata=user_metadata,
                           admin_level=admin_level)


@settings.route("/settings/new_token", methods=['GET'])
@login_required
@login_user
def new_token():
    Users.generate_new_token(current_user.get_id())
    return redirect(url_for('settings.edit_profile'))

@settings.route("/settings/create_user", methods=['GET'])
@login_required
@login_admin
def create_user():
    user_id = request.args.get('user_id')
    error = request.args.get('error')
    error_mail = request.args.get('error_mail')
    role = None
    if user_id:
        user = Users.User(user_id)
        if user.exists():
            role = user.get_role()
    all_roles = Users.get_all_roles()
    return render_template("create_user.html", all_roles=all_roles, user_id=user_id, user_role=role,
                           error=error, error_mail=error_mail,
                           admin_level=True)


@settings.route("/settings/create_user_post", methods=['POST'])
@login_required
@login_admin
def create_user_post():
    email = request.form.get('username')
    role = request.form.get('user_role')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    all_roles = Users.get_all_roles()

    if email and len(email) < 300 and check_email(email) and role:
        if role in all_roles:
            # password set
            if password1 and password2:
                if password1 == password2:
                    if Users.check_password_strength(password1):
                        password = password1
                    else:
                        return render_template("create_user.html", all_roles=all_roles, error="Incorrect Password",
                                               admin_level=True)
                else:
                    return render_template("create_user.html", all_roles=all_roles, error="Passwords don't match",
                                           admin_level=True)
            # generate password
            else:
                password = Users.gen_password()

            if current_user.is_in_role('admin'):
                str_password = password
                if Users.exists_user(email):
                    if not password1 and not password2:
                        password = None
                        str_password = 'Password not changed'
                Users.create_user(email, password=password, role=role)
                return redirect(url_for('settings.users_list', new_user=email, new_user_password=str_password))

        else:
            return render_template("create_user.html", all_roles=all_roles, admin_level=True)
    else:
        return render_template("create_user.html", all_roles=all_roles, error_mail=True, admin_level=True)


# @settings.route("/settings/users_list", methods=['GET'])
# @login_required
# @login_admin
# def users_list():
#     all_users = Users.get_users_metadata(Users.get_all_users())
#     new_user = request.args.get('new_user')
#     new_user_dict = {}
#     if new_user:
#         new_user_dict['email'] = new_user
#         new_user_dict['edited'] = request.args.get('new_user_edited')
#         new_user_dict['password'] = request.args.get('new_user_password')
#     return render_template("users_list.html", all_users=all_users, new_user=new_user_dict, admin_level=True)


@settings.route("/settings/edit_user", methods=['POST'])
@login_required
@login_admin
def edit_user():
    user_id = request.form.get('user_id')
    return redirect(url_for('settings.create_user', user_id=user_id))


@settings.route("/settings/passivedns", methods=['GET'])
@login_required
@login_read_only
def passive_dns():
    passivedns_enabled = d4.is_passive_dns_enabled()
    return render_template("passive_dns.html", passivedns_enabled=passivedns_enabled)


@settings.route("/settings/passivedns/change_state", methods=['GET'])
@login_required
@login_admin
def passive_dns_change_state():
    new_state = request.args.get('state') == 'enable'
    passivedns_enabled = d4.change_passive_dns_state(new_state)
    return redirect(url_for('settings.passive_dns'))


@settings.route("/settings/ail", methods=['GET'])
@login_required
@login_admin
def ail_configs():
    return render_template("ail_configs.html", passivedns_enabled=None)


# ========= REGISTRATION =========
app.register_blueprint(settings, url_prefix=baseUrl)
