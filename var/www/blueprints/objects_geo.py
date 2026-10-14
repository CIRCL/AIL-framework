"""Session-authenticated object geolocation operations for the map UI."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from geo_helpers import get_geo_csrf_token, read_geo_payload, valid_geo_csrf
from lib import geo_api

objects_geo = Blueprint('objects_geo', __name__)


@objects_geo.before_request
def check_geo_session_access():
    if not current_user.is_authenticated:
        return jsonify(status='error', reason='Authentication needed'), 401
    write = request.method not in {'GET', 'HEAD', 'OPTIONS'}
    if not current_user.is_in_role('user_no_api' if write else 'read_only'):
        return jsonify(status='error', reason='Access Forbidden'), 403
    if write and not valid_geo_csrf(current_user.get_user_id()):
        return jsonify(status='error', reason='Invalid CSRF token'), 403


@objects_geo.after_request
def geo_no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@objects_geo.app_template_global('geo_csrf_token')
def geo_csrf_token():
    if not current_user.is_authenticated:
        return ''
    return get_geo_csrf_token(current_user.get_user_id())


@objects_geo.app_template_global('get_object_geo_count')
def get_object_geo_count(gid):
    if not current_user.is_authenticated:
        return {'status': 'error', 'reason': 'Authentication needed'}
    data, _ = geo_api.count_geolocations(gid, current_user.get_user_id(), current_user.get_role(), api=False)
    return data


@objects_geo.route('/objects/geolocations/csrf', methods=['GET'])
def get_geolocation_csrf():
    return jsonify(csrf_token=get_geo_csrf_token(current_user.get_user_id()))


@objects_geo.route('/objects/geolocations/view', methods=['GET'])
def view_geolocations():
    gid = request.args.get('gid')
    data, status = geo_api.count_geolocations(gid, current_user.get_user_id(), current_user.get_role(), api=False)
    if status != 200:
        return jsonify(data), status
    return render_template('geolocation/geolocations.html', geo_gid=data['gid'], geo_count=data['total'])


@objects_geo.route('/objects/geolocations', methods=['GET'])
def list_geolocations():
    data, status = geo_api.list_geolocations(request.args.get('gid'), current_user.get_user_id(), current_user.get_role(), offset=request.args.get('offset'), limit=request.args.get('limit'), api=False)
    return jsonify(data), status


@objects_geo.route('/objects/geolocations/<geo_id>', methods=['GET'])
def get_geolocation(geo_id):
    data, status = geo_api.get_geolocation(request.args.get('gid'), geo_id, current_user.get_user_id(), current_user.get_role(), api=False)
    return jsonify(data), status


@objects_geo.route('/objects/geolocations', methods=['POST'])
def create_geolocation():
    payload, error = read_geo_payload()
    if error:
        return jsonify(error[0]), error[1]
    data, status = geo_api.create_geolocation(request.args.get('gid'), payload, current_user.get_user_id(), current_user.get_role(), api=False)
    return jsonify(data), status


@objects_geo.route('/objects/geolocations/<geo_id>', methods=['PATCH'])
def update_geolocation(geo_id):
    payload, error = read_geo_payload()
    if error:
        return jsonify(error[0]), error[1]
    data, status = geo_api.update_geolocation(request.args.get('gid'), geo_id, payload, current_user.get_user_id(), current_user.get_role(), api=False)
    return jsonify(data), status


@objects_geo.route('/objects/geolocations/<geo_id>', methods=['DELETE'])
def delete_geolocation(geo_id):
    payload, error = read_geo_payload(required=False)
    if error:
        return jsonify(error[0]), error[1]
    data, status = geo_api.delete_geolocation(request.args.get('gid'), geo_id, payload, current_user.get_user_id(), current_user.get_role(), api=False)
    return jsonify(data), status
