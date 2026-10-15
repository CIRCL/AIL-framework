#!/usr/bin/python3

"""Shared MISP integration, module client, and object export helpers for AIL."""

import os
import json
import requests
import sys
import logging
import math
import copy
import uuid
from redis.exceptions import RedisError
from datetime import date, datetime, timezone
from urllib.parse import urlsplit, urlunsplit

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn('Kvrocks_DB')
config_loader = None

MISP_EXPORT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.ail-project.org/misp')
logger = logging.getLogger(__name__)


def normalize_seen(value):
    """Convert an AIL calendar date or datetime to UTC, leaving unknown dates unset."""
    if value is None or value == '':
        return None
    try:
        if isinstance(value, datetime):
            observed = value
        elif isinstance(value, date):
            observed = datetime.combine(value, datetime.min.time())
        else:
            value = str(value)
            if len(value) == 8 and value.isdigit():
                observed = datetime.strptime(value, '%Y%m%d')
            else:
                observed = datetime.fromisoformat(value.replace('/', '-'))
    except (TypeError, ValueError):
        logger.warning('Invalid AIL observation date %r; omitting it from the MISP export', value)
        return None
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc)


def finalize_misp_object(obj, global_id, tags, first_seen=None, last_seen=None):
    """Set random object UUIDs, unique attribute identities, dates, and tags."""
    obj.uuid = str(uuid.uuid4())
    first_seen = normalize_seen(first_seen)
    last_seen = normalize_seen(last_seen)
    if first_seen and last_seen and last_seen < first_seen:
        logger.warning('Inverted observation dates for %s; omitting last_seen from the MISP export', global_id)
        last_seen = None
    if first_seen is not None:
        obj.first_seen = first_seen
    if last_seen is not None:
        obj.last_seen = last_seen
    for attribute in obj.attributes:
        attribute_identity = json.dumps([obj.uuid, attribute.object_relation, attribute.type, attribute.value], ensure_ascii=False, separators=(',', ':'))
        attribute.uuid = str(uuid.uuid5(MISP_EXPORT_NAMESPACE, attribute_identity))
        for tag in tags:
            attribute.add_tag(tag)
    return obj


SUPPORTED_MODULES = {
    'onion_lookup': (),
    'circl_passivedns': ('username', 'password'),
    'circl_passivessl': ('username', 'password'),
    'passive_ssh': ('api_user', 'api_key'),
    'hashlookup': (),
    'ipasn': (),
    'dns': (),
    'reversedns': (),
    'extract_url_components': (),
}
SERVICE_DEFAULTS = {'enabled': 'false', 'url': 'http://127.0.0.1', 'port': '6666', 'timeout': '30'}
OPTIONAL_MODULE_CONFIG_FIELDS = {
    'passive_ssh': ('custom_api_url',),
    'hashlookup': ('custom_API',),
    'ipasn': ('custom_api',),
    'dns': ('nameserver',),
    'reversedns': ('nameserver',),
}
BOOLEAN_VALUES = {'1': True, 'yes': True, 'true': True, 'on': True, '0': False, 'no': False, 'false': False, 'off': False}
MODULE_DESCRIPTIONS = {
    'onion_lookup': 'Look up known information about a Tor onion service.',
    'circl_passivedns': 'Find historical DNS observations for domains and IP addresses.',
    'circl_passivessl': 'Find certificates observed on an IP address.',
    'passive_ssh': 'Find observed SSH fingerprints and their hosts.',
    'hashlookup': 'Look up a file hash in known-file datasets.',
    'ipasn': 'Find the autonomous system associated with an IP address.',
    'dns': 'Resolve a domain using DNS.',
    'reversedns': 'Look up the reverse DNS name of an IP address.',
    'extract_url_components': 'Extract the components of a recorded URL.',
}
EXPANSION_OBJECT_TYPES = {'domain', 'ip', 'ssh-key', 'decoded', 'item'}
EXPANSION_ATTRIBUTE_TYPES = {'domain', 'hostname', 'onion-address', 'ip-src', 'ip-dst', 'ip', 'ssh-fingerprint', 'md5', 'sha1', 'sha256', 'url', 'domain|ip', 'ip-src|port', 'ip-dst|port'}
EMPTY_MODULE_ERRORS = {'not found', 'empty result', 'empty results', 'non existing hash', 'nxdomain', 'unable to find the history of this ip'}


class MISPModuleError(Exception):
    """An actionable error that can safely be returned to an analyst."""

    def __init__(self, message, code='module_error', status=502):
        super().__init__(message)
        self.code = code
        self.status = status

    def to_dict(self):
        return {'status': 'error', 'code': self.code, 'reason': str(self)}


def get_module_config_fields(module):
    """Normalize legacy field lists and richer module configuration metadata."""
    fields = module['meta'].get('config', [])
    if not isinstance(fields, (list, dict)):
        raise MISPModuleError('Invalid module configuration metadata.', 'invalid_response')
    entries = fields.items() if isinstance(fields, dict) else enumerate(fields)
    normalized = []
    names = set()
    for key, definition in entries:
        if isinstance(definition, dict):
            name = key if isinstance(key, str) else definition.get('name')
            field = {k: definition[k] for k in ('type', 'description', 'required', 'redacted', 'null') if k in definition}
        elif isinstance(definition, str):
            name = key if isinstance(key, str) else definition
            field = {'description': definition} if isinstance(key, str) else {}
        else:
            raise MISPModuleError('Invalid module configuration metadata.', 'invalid_response')
        if not isinstance(name, str) or not name or name == 'enabled' or name in names or any(character in name for character in '\r\n=[]:') or name.startswith(('#', ';')):
            raise MISPModuleError('Invalid module configuration field.', 'invalid_response')
        names.add(name)
        field['name'] = name
        field.setdefault('type', 'string')
        field['required'] = name in SUPPORTED_MODULES[module['name']] or field.get('required') is True or field.get('null') is False
        normalized.append(field)
    return normalized


def is_secret_config_field(field, include_usernames=False):
    name = field['name'].lower()
    return field.get('redacted') is True or field.get('type') == 'password' or (include_usernames and name in ('username', 'api_user')) or any(term in name for term in ('password', 'secret', 'token', 'key'))


def mask_config_value(value):
    if value is None:
        return None
    value = str(value)
    if len(value) <= 4:
        return '*' * len(value)
    return value[:2] + '*' * (len(value) - 4) + value[-2:]


def _builtin_module_definition(name):
    """Use known configuration fields while the service is unavailable."""
    fields = list(SUPPORTED_MODULES[name]) + list(OPTIONAL_MODULE_CONFIG_FIELDS.get(name, ()))
    return {'name': name, 'meta': {'description': MODULE_DESCRIPTIONS[name], 'config': fields}, 'mispattributes': {}}


def _validate_attribute(attribute):
    if not isinstance(attribute, dict) or not isinstance(attribute.get('type'), str) or not attribute['type'] or 'value' not in attribute:
        raise MISPModuleError('Invalid attribute in the module response.', 'invalid_response')
    if not isinstance(attribute['value'], (str, int, float)) or isinstance(attribute['value'], bool):
        raise MISPModuleError('Invalid attribute value in the module response.', 'invalid_response')


def parse_module_enrichment_response(response):
    """Preserve typed records, objects, references, tags, and other MISP metadata."""
    if not isinstance(response, dict):
        raise MISPModuleError('The module returned an invalid response.', 'invalid_response')
    if 'error' in response:
        reason = str(response['error']).strip().lower().rstrip('.')
        if reason in EMPTY_MODULE_ERRORS:
            return {'format': 'misp_standard', 'results': {}}
        if 'timeout' in reason:
            raise MISPModuleError('The module lookup timed out.', 'timeout', 504)
        if 'rate limit' in reason or 'too many requests' in reason:
            raise MISPModuleError('The module provider rate limit was reached.', 'rate_limited', 429)
        if any(word in reason for word in ('authenticat', 'credential', 'password', 'user required')):
            raise MISPModuleError('The module provider rejected its configuration or credentials.', 'provider_authentication')
        # Provider errors may echo configuration; never forward their raw text.
        raise MISPModuleError('The module could not complete the lookup.', 'module_error')
    if 'results' not in response:
        raise MISPModuleError('The module response has no results field.', 'invalid_response')
    results = response['results']
    if isinstance(results, list):
        for record in results:
            if not isinstance(record, dict) or not isinstance(record.get('types'), list) or not record['types'] or not all(isinstance(t, str) and t for t in record['types']) or not isinstance(record.get('values'), list):
                raise MISPModuleError('The module returned invalid legacy results.', 'invalid_response')
            if not all(isinstance(v, (str, int, float)) and not isinstance(v, bool) for v in record['values']):
                raise MISPModuleError('The module returned invalid legacy values.', 'invalid_response')
        return {'format': 'legacy', 'results': copy.deepcopy(results)}
    if not isinstance(results, dict):
        raise MISPModuleError('The module returned an unsupported result format.', 'invalid_response')
    if results and not any(key in results for key in ('Attribute', 'Object', 'Tag', 'Galaxy', 'EventReport')):
        raise MISPModuleError('The module returned an unsupported result format.', 'invalid_response')
    for key in ('Attribute', 'Object', 'Tag', 'Galaxy', 'EventReport'):
        if key in results and not isinstance(results[key], list):
            raise MISPModuleError('The module returned invalid MISP collections.', 'invalid_response')
    for attribute in results.get('Attribute', []):
        _validate_attribute(attribute)
    for obj in results.get('Object', []):
        if not isinstance(obj, dict) or not isinstance(obj.get('name'), str) or not obj['name'] or not isinstance(obj.get('uuid'), str) or not obj['uuid'] or not isinstance(obj.get('Attribute'), list):
            raise MISPModuleError('The module returned an invalid MISP object.', 'invalid_response')
        for attribute in obj['Attribute']:
            _validate_attribute(attribute)
        if not isinstance(obj.get('ObjectReference', []), list):
            raise MISPModuleError('The module returned invalid object references.', 'invalid_response')
        for reference in obj.get('ObjectReference', []):
            if not isinstance(reference, dict) or not isinstance(reference.get('referenced_uuid'), str) or not isinstance(reference.get('relationship_type'), str):
                raise MISPModuleError('The module returned invalid object references.', 'invalid_response')
    return {'format': 'misp_standard', 'results': copy.deepcopy(results)}


def get_expansion_object(global_id):
    """Resolve an existing AIL object; transient graph nodes are not accepted."""
    if not isinstance(global_id, str):
        raise MISPModuleError('An AIL object global ID is required.', 'invalid_object', 400)
    parts = global_id.split(':', 2)
    if len(parts) != 3 or parts[0] not in EXPANSION_OBJECT_TYPES or parts[1] or not parts[2]:
        raise MISPModuleError('This object is not supported for expansion.', 'invalid_object', 400)
    # Local import avoids a cycle with the object exporters using this library.
    from lib.objects import ail_objects
    obj = ail_objects.get_object(*parts)
    if not obj.exists():
        raise MISPModuleError('The AIL object does not exist.', 'object_not_found', 404)
    return obj


def get_expansion_inputs(obj):
    """Reuse semantic exports while keeping attachments out of lookup inputs."""
    if obj.get_type() not in EXPANSION_OBJECT_TYPES:
        raise MISPModuleError('This AIL object is not supported for expansion.', 'invalid_object', 400)
    try:
        if obj.get_type() == 'decoded':
            objects = [obj.get_misp_object(include_data=False)]
        elif obj.get_type() == 'item':
            objects = obj.get_misp_objects(include_data=False)
        else:
            objects = obj.get_misp_objects()
    except (ValueError, FileNotFoundError):
        raise MISPModuleError('Unable to export this AIL object for expansion.', 'invalid_input', 400) from None
    inputs = []
    for misp_object in objects:
        for attribute in misp_object.attributes:
            if attribute.type in EXPANSION_ATTRIBUTE_TYPES:
                identity = json.dumps([obj.get_global_id(), misp_object.name, attribute.object_relation, attribute.type, attribute.value], ensure_ascii=False, separators=(',', ':'))
                input_id = str(uuid.uuid5(MISP_EXPORT_NAMESPACE, identity))
                inputs.append({'id': input_id, 'uuid': attribute.uuid, 'type': attribute.type, 'value': attribute.value, 'object_relation': attribute.object_relation, 'object_name': misp_object.name, 'object_uuid': misp_object.uuid})
    return objects, inputs


class MISPModuleClient:
    """Read-only module discovery and transient lookups using server configuration."""

    def __init__(self, http=None, db=None):
        self.db = db if db is not None else r_db
        self.http = http if http is not None else requests

    def _settings(self, section):
        try:
            if section == 'misp_modules':
                return SERVICE_DEFAULTS | self.db.hgetall('misp:modules:service')
            return self.db.hgetall(f'misp:modules:config:{section}')
        except RedisError:
            raise MISPModuleError('Unable to read MISP module settings from Kvrocks.', 'configuration_error', 503) from None

    def _boolean(self, section, name, settings=None):
        settings = self._settings(section) if settings is None else settings
        try:
            return BOOLEAN_VALUES[settings.get(name, 'false').lower()]
        except (KeyError, AttributeError):
            raise MISPModuleError('Invalid module activation setting.', 'configuration_error', 503) from None

    def _connection(self, require_enabled=True, settings=None):
        settings = self._settings('misp_modules') if settings is None else settings
        if require_enabled and not self._boolean('misp_modules', 'enabled', settings):
            raise MISPModuleError('MISP module expansion is disabled.', 'service_disabled', 503)
        try:
            parts = urlsplit(settings['url'])
            if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
                raise ValueError
            netloc = parts.netloc
            port = settings['port'].strip()
            if parts.port is None and port:
                if not 0 < int(port) < 65536:
                    raise ValueError
                netloc = f'{netloc}:{port}'
            timeout = float(settings['timeout'])
            if not math.isfinite(timeout) or timeout <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise MISPModuleError('Invalid MISP module service connection settings.', 'configuration_error', 503) from None
        return urlunsplit((parts.scheme, netloc, parts.path.rstrip('/'), '', '')), timeout

    def _request(self, method, path, payload=None, require_enabled=True):
        base_url, timeout = self._connection(require_enabled=require_enabled)
        try:
            if method == 'GET':
                response = self.http.get(f'{base_url}/{path}', timeout=(timeout, timeout), allow_redirects=False)
            else:
                response = self.http.post(f'{base_url}/{path}', json=payload, timeout=(timeout, timeout), allow_redirects=False)
        except requests.Timeout:
            raise MISPModuleError('The MISP module service timed out.', 'timeout', 504) from None
        except requests.RequestException:
            raise MISPModuleError('The MISP module service is unreachable.', 'service_unreachable', 503) from None
        if response.status_code in (401, 403):
            raise MISPModuleError('The MISP module service rejected authentication.', 'service_authentication')
        if response.status_code == 429:
            raise MISPModuleError('The MISP module service rate limit was reached.', 'rate_limited', 429)
        if response.status_code in (408, 504):
            raise MISPModuleError('The MISP module service timed out.', 'timeout', 504)
        if response.status_code != 200:
            raise MISPModuleError('The MISP module service returned an HTTP error.', 'service_http_error')
        try:
            return response.json()
        except ValueError:
            raise MISPModuleError('The MISP module service returned invalid JSON.', 'invalid_response') from None

    def get_modules(self, require_enabled=True):
        response = self._request('GET', 'modules', require_enabled=require_enabled)
        if not isinstance(response, list):
            raise MISPModuleError('The service returned an invalid module list.', 'invalid_response')
        modules = []
        names = set()
        for module in response:
            if not isinstance(module, dict) or module.get('name') not in SUPPORTED_MODULES:
                continue
            meta = module.get('meta')
            attributes = module.get('mispattributes')
            if not isinstance(meta, dict) or not isinstance(meta.get('module-type'), list) or not isinstance(attributes, dict) or not isinstance(attributes.get('input'), list) or not all(isinstance(t, str) for t in attributes['input']):
                raise MISPModuleError('The service returned invalid module metadata.', 'invalid_response')
            if 'expansion' not in meta['module-type']:
                continue
            if module['name'] in names:
                raise MISPModuleError('The service returned duplicate module names.', 'invalid_response')
            get_module_config_fields(module)
            names.add(module['name'])
            modules.append(module)
        return sorted(modules, key=lambda module: module['name'])

    def _config_values(self, module, configured=None):
        values = {}
        configured = self._settings(module['name']) if configured is None else configured
        for field in get_module_config_fields(module):
            name = field['name']
            value = configured.get(name)
            if value is not None and value.strip():
                if field['type'] in ('boolean', 'bool'):
                    try:
                        value = BOOLEAN_VALUES[value.lower()]
                    except KeyError:
                        raise MISPModuleError('Invalid boolean module setting.', 'configuration_error', 503) from None
                elif field['type'] in ('integer', 'int', 'number', 'float'):
                    try:
                        value = int(value) if field['type'] in ('integer', 'int') else float(value)
                        if not math.isfinite(value):
                            raise ValueError
                    except ValueError:
                        raise MISPModuleError('Invalid numeric module setting.', 'configuration_error', 503) from None
                values[name] = value
        return values

    def _save_settings(self, section, values):
        if not values:
            return
        try:
            if section == 'misp_modules':
                self.db.hset('misp:modules:service', mapping=values)
            else:
                self.db.hset(f'misp:modules:config:{section}', mapping=values)
        except RedisError:
            raise MISPModuleError('Unable to save MISP module settings in Kvrocks.', 'configuration_write_error', 503) from None

    def save_service_settings(self, settings):
        if not isinstance(settings, dict) or not settings or set(settings) - {'enabled', 'url', 'port', 'timeout'}:
            raise MISPModuleError('Expected service activation, URL, port, or timeout.', 'invalid_settings', 400)
        if 'enabled' in settings and not isinstance(settings['enabled'], bool):
            raise MISPModuleError('Service activation must be a boolean.', 'invalid_settings', 400)
        for key in ('url', 'port', 'timeout'):
            if key in settings and (not isinstance(settings[key], (str, int, float)) or isinstance(settings[key], bool) or '\n' in str(settings[key]) or '\r' in str(settings[key])):
                raise MISPModuleError('Invalid service connection setting.', 'invalid_settings', 400)

        values = {key: str(value).lower() if isinstance(value, bool) else str(value).strip() for key, value in settings.items()}
        candidate = self._settings('misp_modules') | values
        try:
            self._connection(require_enabled=False, settings=candidate)
        except MISPModuleError:
            raise MISPModuleError('Use an HTTP(S) URL, a valid port, and a positive timeout.', 'invalid_settings', 400) from None
        self._save_settings('misp_modules', values)

    def save_module_settings(self, name, settings):
        if name not in SUPPORTED_MODULES:
            raise MISPModuleError('This expansion module is not supported.', 'unsupported_module', 400)
        if not isinstance(settings, dict) or not settings or set(settings) - {'enabled', 'config'}:
            raise MISPModuleError('Expected module activation or configuration.', 'invalid_settings', 400)
        if 'enabled' in settings and not isinstance(settings['enabled'], bool):
            raise MISPModuleError('Module activation must be a boolean.', 'invalid_settings', 400)
        fields = settings.get('config', {})
        if not isinstance(fields, dict):
            raise MISPModuleError('Module configuration must be an object.', 'invalid_settings', 400)
        definition = _builtin_module_definition(name)
        if fields:
            try:
                definition = next((module for module in self.get_modules(require_enabled=False) if module['name'] == name), definition)
            except MISPModuleError:
                # Administrators can prepare known settings before starting the service.
                pass
        allowed = {field['name'] for field in get_module_config_fields(definition)}
        if set(fields) - allowed:
            raise MISPModuleError('Configuration contains fields not advertised by this module. Refresh the service metadata.', 'invalid_settings', 400)
        for value in fields.values():
            if value is not None and (not isinstance(value, (str, int, float, bool)) or '\n' in str(value) or '\r' in str(value)):
                raise MISPModuleError('Invalid module configuration value.', 'invalid_settings', 400)

        values = {key: '' if value is None else str(value).lower() if isinstance(value, bool) else str(value) for key, value in fields.items()}
        if 'enabled' in settings:
            values['enabled'] = str(settings['enabled']).lower()
        candidate = self._settings(name) | values
        try:
            self._config_values(definition, configured=candidate)
        except MISPModuleError:
            raise MISPModuleError('Check the types of the module configuration values.', 'invalid_settings', 400) from None
        self._save_settings(name, values)

    def get_settings(self, check_connection=False):
        """Administrator settings with readable options and masked secret previews."""
        definitions = {}
        health = 'not_checked'
        error = None
        checked_at = None
        if check_connection:
            checked_at = datetime.now(timezone.utc).isoformat()
            try:
                definitions = {module['name']: module for module in self.get_modules(require_enabled=False)}
                health = 'available'
            except MISPModuleError as failure:
                health = 'unavailable'
                error = failure.to_dict()
        configured_service = self._settings('misp_modules')
        service = {key: configured_service[key] for key in ('url', 'port', 'timeout')}
        service.update(enabled=self._boolean('misp_modules', 'enabled', configured_service), health=health, error=error, checked_at=checked_at)
        modules = []
        for name in sorted(SUPPORTED_MODULES):
            definition = definitions.get(name) or _builtin_module_definition(name)
            configured = self._settings(name)
            values = self._config_values(definition, configured)
            missing = self._missing_config(definition, values)
            fields = []
            for field in get_module_config_fields(definition):
                secret = is_secret_config_field(field)
                value = values.get(field['name'])
                fields.append({**field, 'secret': secret, 'configured': field['name'] in values, 'value': None if secret else value, 'masked_value': mask_config_value(value) if secret else None})
            enabled = self._boolean(name, 'enabled', configured)
            discovered = name in definitions if health == 'available' else None
            supported_format = definition['mispattributes'].get('format') in (None, 'misp_standard')
            state = 'needs_configuration' if missing else 'unsupported_format' if not supported_format else 'unavailable' if discovered is False else 'enabled' if enabled else 'disabled'
            modules.append({'name': name, 'label': definition['meta'].get('name') or name, 'description': definition['meta'].get('description', MODULE_DESCRIPTIONS[name]), 'enabled': enabled, 'discovered': discovered, 'metadata_source': 'service' if name in definitions else 'builtin', 'configuration_status': state, 'missing_configuration': missing, 'fields': fields})
        return {'status': 'success', 'service': service, 'modules': modules}

    def _missing_config(self, module, values):
        required = set(SUPPORTED_MODULES[module['name']])
        required.update(field['name'] for field in get_module_config_fields(module) if field['required'])
        return sorted(name for name in required if name not in values)

    def list_expansion_modules(self):
        """Public discovery metadata for native graph pivots, without credentials."""
        options = []
        for module in self.get_modules():
            configured = self._settings(module['name'])
            values = self._config_values(module, configured)
            enabled = self._boolean(module['name'], 'enabled', configured)
            missing = self._missing_config(module, values)
            supported_format = module['mispattributes'].get('format') in (None, 'misp_standard')
            options.append({'name': module['name'], 'label': module['meta'].get('name') or module['name'], 'description': module['meta'].get('description', ''), 'enabled': enabled, 'available': enabled and not missing and supported_format, 'missing_configuration': missing, 'supported_format': supported_format, 'input_types': module['mispattributes']['input']})
        return {'status': 'success', 'modules': options}

    def list_expansions(self, obj):
        _, inputs = get_expansion_inputs(obj)
        options = []
        for module in self.list_expansion_modules()['modules']:
            compatible = [item for item in inputs if item['type'] in module['input_types']]
            if compatible:
                options.append({k: v for k, v in module.items() if k != 'input_types'} | {'inputs': [{k: v for k, v in item.items() if k not in ('uuid', 'object_uuid')} for item in compatible]})
        return {'status': 'success', 'object_id': obj.get_global_id(), 'modules': options}

    def build_request(self, module, attribute):
        name = module['name']
        if name not in SUPPORTED_MODULES:
            raise MISPModuleError('This expansion module is not supported.', 'unsupported_module', 400)
        if not self._boolean(name, 'enabled'):
            raise MISPModuleError('This expansion module is disabled.', 'module_disabled', 403)
        if attribute['type'] not in module['mispattributes']['input']:
            raise MISPModuleError('The module does not accept this input type.', 'invalid_input', 400)
        values = self._config_values(module)
        missing = self._missing_config(module, values)
        if missing:
            raise MISPModuleError('Required module configuration is missing: ' + ', '.join(missing), 'module_not_configured', 503)
        payload = {'module': name, 'config': values}
        format_name = module['mispattributes'].get('format')
        if format_name == 'misp_standard':
            payload['attribute'] = {key: attribute[key] for key in ('type', 'value', 'uuid')}
        elif format_name is None:
            payload[attribute['type']] = attribute['value']
        else:
            raise MISPModuleError('The module uses an unsupported input format.', 'unsupported_format', 400)
        return payload

    def expand(self, obj, module_name, input_id=None):
        if not isinstance(module_name, str) or module_name not in SUPPORTED_MODULES:
            raise MISPModuleError('This expansion module is not supported.', 'unsupported_module', 400)
        if not self._boolean(module_name, 'enabled'):
            raise MISPModuleError('This expansion module is disabled.', 'module_disabled', 403)
        module = next((module for module in self.get_modules() if module['name'] == module_name), None)
        if module is None:
            raise MISPModuleError('The module is not available on the service.', 'module_unavailable', 503)
        objects, inputs = get_expansion_inputs(obj)
        compatible = [item for item in inputs if item['type'] in module['mispattributes']['input']]
        if input_id is not None:
            compatible = [item for item in compatible if item['id'] == input_id]
        if not compatible:
            raise MISPModuleError('No compatible exported input was selected.', 'invalid_input', 400)
        if len(compatible) != 1:
            raise MISPModuleError('Select one compatible exported input.', 'input_required', 400)
        selected = compatible[0]
        payload = self.build_request(module, selected)
        parsed = parse_module_enrichment_response(self._request('POST', 'query', payload))
        # Remove any credential echoed by a provider before exposing results.
        secret_fields = {field['name'] for field in get_module_config_fields(module) if is_secret_config_field(field, include_usernames=True)}
        secrets = [value for key, value in payload['config'].items() if isinstance(value, str) and key in secret_fields]
        parsed['results'] = _redact_credentials(parsed['results'], secrets)
        if parsed['format'] == 'legacy':
            has_results = any(record['values'] for record in parsed['results'])
        else:
            has_results = any(parsed['results'].get(key) for key in ('Object', 'Tag', 'Galaxy', 'EventReport')) or any(attribute.get('uuid') != selected['uuid'] for attribute in parsed['results'].get('Attribute', []))
        return {'status': 'success' if has_results else 'empty', 'module': module_name, 'input': {k: selected[k] for k in ('id', 'uuid', 'type', 'value')}, 'source': {'global_id': obj.get_global_id(), 'object_uuid': objects[0].uuid, 'input_object_uuid': selected['object_uuid'], 'attribute_uuid': selected['uuid']}, 'executed_at': datetime.now(timezone.utc).isoformat(), **parsed}


def _redact_credentials(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, '[redacted]')
        return value
    if isinstance(value, list):
        return [_redact_credentials(item, secrets) for item in value]
    if isinstance(value, dict):
        return {_redact_credentials(key, secrets): _redact_credentials(item, secrets) for key, item in value.items() if key != 'config'}
    return value


def load_modules_list():
    """Discover modules without storing results or rewriting administrator settings."""
    return MISPModuleClient().get_modules()
