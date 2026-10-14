"""JSON and session CSRF handling shared by the object geolocation routes."""

import hmac
import json
import secrets

from flask import request, session

MAX_GEO_JSON_SIZE = 4096


def read_geo_payload(required=True):
    if request.content_length is not None and request.content_length > MAX_GEO_JSON_SIZE:
        return None, ({'status': 'error', 'reason': 'Geolocation request is too large'}, 413)
    content = request.stream.read(MAX_GEO_JSON_SIZE + 1)
    if len(content) > MAX_GEO_JSON_SIZE:
        return None, ({'status': 'error', 'reason': 'Geolocation request is too large'}, 413)
    if not content and not required:
        return {}, None
    if not request.is_json:
        return None, ({'status': 'error', 'reason': 'Content-Type must be application/json'}, 415)
    try:
        data = json.loads(content)
    except (ValueError, UnicodeDecodeError):
        return None, ({'status': 'error', 'reason': 'Invalid JSON body'}, 400)
    if not isinstance(data, dict):
        return None, ({'status': 'error', 'reason': 'Expected a JSON object'}, 400)
    return data, None


def get_geo_csrf_token(user_id):
    stored = session.get('geo_csrf')
    if not isinstance(stored, dict) or stored.get('user_id') != user_id or not isinstance(stored.get('token'), str):
        stored = {'user_id': user_id, 'token': secrets.token_urlsafe(32)}
        session['geo_csrf'] = stored
    return stored['token']


def valid_geo_csrf(user_id):
    stored = session.get('geo_csrf')
    supplied = request.headers.get('X-CSRF-Token')
    if not isinstance(stored, dict) or stored.get('user_id') != user_id or not isinstance(stored.get('token'), str):
        return False
    if not supplied or not supplied.isascii() or not stored['token'].isascii():
        return False
    return hmac.compare_digest(stored['token'], supplied)
