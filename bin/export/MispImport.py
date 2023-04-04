#!/usr/bin/env python3
# -*-coding:UTF-8 -*

# import os
# import sys
# import uuid
#
# from hashlib import sha1, sha256
#
# sys.path.append(os.environ['AIL_BIN'])
# from lib.objects import ail_objects
#
#
# from lib.objects import Items
#
# # MISP
# from pymisp import MISPEvent, MISPObject, PyMISP
#
# # # TODO: deplace me in another fil
# def get_global_id(obj_type, obj_id, obj_subtype=None):
#     if obj_subtype:
#         return '{}:{}:{}'.format(obj_type, obj_subtype, obj_id)
#     else:
#         return '{}:{}'.format(obj_type, obj_id)
#
# # sub type
# # obj type
# # obj value
# def get_global_id_from_id(global_id):
#     obj_meta = {}
#     global_id = global_id.split(':', 3)
#     if len(global_id) > 2:
#         obj_meta['type'] = global_id[0]
#         obj_meta['subtype'] = global_id[1]
#         obj_meta['id'] = global_id[2]
#     else:
#         obj_meta['type'] = global_id[0]
#         obj_meta['subtype'] = ''
#         obj_meta['id'] = global_id[1]
#     return obj_meta
#
# def get_import_dir():
#     return os.path.join(os.environ['AIL_HOME'], 'temp/import')
#
# def sanitize_import_file_path(filename):
#     IMPORT_FOLDER = get_import_dir()
#     filename = os.path.join(IMPORT_FOLDER, filename)
#     filename = os.path.realpath(filename)
#     # path traversal
#     if not os.path.commonprefix([filename, IMPORT_FOLDER]) == IMPORT_FOLDER:
#         return os.path.join(IMPORT_FOLDER, str(uuid.uuid4()) + '.json')
#     # check if file already exist
#     if os.path.isfile(filename):
#         return os.path.join(IMPORT_FOLDER, str(uuid.uuid4()) + '.json')
#     return filename
#
# def get_misp_obj_tag(misp_obj):
#     if misp_obj.attributes:
#         misp_tags = misp_obj.attributes[0].tags
#         tags = []
#         for misp_tag in misp_tags:
#             tags.append(misp_tag.name)
#         return tags
#     else:
#         return []
#
# def get_object_metadata(misp_obj):
#     obj_meta = {}
#     if 'first_seen' in misp_obj.keys():
#         obj_meta['first_seen'] = misp_obj.first_seen
#     if 'last_seen' in misp_obj.keys():
#         obj_meta['last_seen'] = misp_obj.last_seen
#     obj_meta['tags'] = get_misp_obj_tag(misp_obj)
#     return obj_meta
#
# def unpack_item_obj(map_uuid_global_id, misp_obj):
#     obj_meta = get_object_metadata(misp_obj)
#     obj_id = None
#     io_content = None
#
#     for attribute in misp_obj.attributes:
#         if attribute.object_relation == 'raw-data':
#             obj_id = attribute.value               # # TODO: sanitize
#             io_content = attribute.data             # # TODO: check if type == io
#
#     if obj_id and io_content:
#         res = Items.create_item(obj_id, obj_meta, io_content)
#
#         map_uuid_global_id[misp_obj.uuid] = get_global_id('item', obj_id)
#
#
#
# ## TODO: handle multiple pgp in the same object
# def unpack_obj_pgp(map_uuid_global_id, misp_obj):
#     # TODO ail_objects   import_misp_object(misp_obj)
#     pass
#     # # get obj sub type
#     # obj_attr = misp_obj.attributes[0]
#     # obj_id = obj_attr.value
#     # if obj_attr.object_relation == 'key-id':
#     #     obj_subtype = 'key'
#     # elif obj_attr.object_relation == 'user-id-name':
#     #     obj_subtype = 'name'
#     # elif obj_attr.object_relation == 'user-id-email':
#     #     obj_subtype = 'mail'
#     #
#     # if obj_id and obj_subtype:
#     #     obj_meta = get_object_metadata(misp_obj)
#     #     # res = Pgp.pgp.create_correlation(obj_subtype, obj_id, obj_meta)
#     #     # TODO ail_objects   import_misp_object(misp_obj)
#     #
#     #     map_uuid_global_id[misp_obj.uuid] = get_global_id('pgp', obj_id, obj_subtype=obj_subtype)
#
#
# def unpack_obj_cryptocurrency(map_uuid_global_id, misp_obj):
#     # TODO ail_objects   import_misp_object(misp_obj)
#     pass
#     #
#     # obj_id = None
#     # obj_subtype = None
#     # for attribute in misp_obj.attributes:
#     #     if attribute.object_relation == 'address': # # TODO: handle xmr address field
#     #         obj_id = attribute.value
#     #     elif attribute.object_relation == 'symbol':
#     #         obj_subtype = Cryptocurrency.get_cryptocurrency_type(attribute.value)
#     #
#     # # valid cryptocurrency type
#     # if obj_subtype and obj_id:
#     #     obj_meta = get_object_metadata(misp_obj)
#     #     # res = Cryptocurrency.cryptocurrency.create_correlation(obj_subtype, obj_id, obj_meta)
#     #
#     #     map_uuid_global_id[misp_obj.uuid] = get_global_id('cryptocurrency', obj_id, obj_subtype=obj_subtype)
#
# def get_obj_type_from_relationship(misp_obj):
#     obj_uuid = misp_obj.uuid
#     obj_type = None
#
#     for relation in misp_obj.ObjectReference:
#         if relation.object_uuid == obj_uuid:
#             if relation.relationship_type == "screenshot-of":
#                 return 'screenshot'
#             if relation.relationship_type == "included-in":
#                 obj_type = 'decoded'
#     return obj_type
#
#
# # # TODO: covert md5 and sha1 to expected
# def unpack_file(map_uuid_global_id, misp_obj):
#
#     obj_type = get_obj_type_from_relationship(misp_obj)
#     if obj_type:
#         obj_id = None
#         io_content = None
#         for attribute in misp_obj.attributes:
#             # get file content
#             if attribute.object_relation == 'attachment':
#                 io_content = attribute.data
#             elif attribute.object_relation == 'malware-sample':
#                 io_content = attribute.data
#
#             # # TODO: use/verify specified mimetype
#             elif attribute.object_relation == 'mimetype':
#                 #print(attribute.value)
#                 pass
#
#             # # TODO: support more
#             elif attribute.object_relation == 'sha1' and obj_type == 'decoded':
#                 obj_id = attribute.value
#             elif attribute.object_relation == 'sha256' and obj_type == 'screenshot':
#                 obj_id = attribute.value
#
#         # get SHA1/sha256
#         if io_content and not obj_id:
#             if obj_type=='screenshot':
#                 obj_id = sha256(io_content.getvalue()).hexdigest()
#             else: # decoded file
#                 obj_id = sha1(io_content.getvalue()).hexdigest()
#
#         if obj_id and io_content:
#             obj_meta = get_object_metadata(misp_obj)
#             if obj_type == 'screenshot':
#                 # TODO MIGRATE + REFACTOR ME
#                 # Screenshot.create_screenshot(obj_id, obj_meta, io_content)
#                 map_uuid_global_id[misp_obj.uuid] = get_global_id('image', obj_id)
#             else: #decoded
#                 # TODO MIGRATE + REFACTOR ME
#                 # Decoded.create_decoded(obj_id, obj_meta, io_content)
#                 map_uuid_global_id[misp_obj.uuid] = get_global_id('decoded', obj_id)
#
#
# def get_misp_import_fct(map_uuid_global_id, misp_obj):
#     if misp_obj.name == 'ail-leak':
#         unpack_item_obj(map_uuid_global_id, misp_obj)
#     elif misp_obj.name == 'domain-crawled':
#         pass
#     elif misp_obj.name == 'pgp-meta':
#         unpack_obj_pgp(map_uuid_global_id, misp_obj)
#     elif misp_obj.name == 'coin-address':
#         unpack_obj_cryptocurrency(map_uuid_global_id, misp_obj)
#     elif misp_obj.name == 'file':
#         unpack_file(map_uuid_global_id, misp_obj)
#
# # import relationship between objects
# def create_obj_relationships(map_uuid_global_id, misp_obj):
#     if misp_obj.uuid in map_uuid_global_id:
#         for relationship in misp_obj.ObjectReference:
#             if relationship.referenced_uuid in map_uuid_global_id:
#                 obj_meta_src = get_global_id_from_id(map_uuid_global_id[relationship.object_uuid])
#                 obj_meta_target = get_global_id_from_id(map_uuid_global_id[relationship.referenced_uuid])
#
#                 if obj_meta_src == 'decoded' or obj_meta_src == 'item':
#                     print('000000')
#                     print(obj_meta_src)
#                     print(obj_meta_target)
#                     print('111111')
#
#                 # TODO CREATE OBJ RELATIONSHIP
#
# def import_objs_from_file(filepath):
#     map_uuid_global_id = {}
#
#     event_to_import = MISPEvent()
#     try:
#         event_to_import.load_file(filepath)
#     except:
#         return map_uuid_global_id
#
#     for misp_obj in event_to_import.objects:
#         get_misp_import_fct(map_uuid_global_id, misp_obj)
#
#     for misp_obj in event_to_import.objects:
#         create_obj_relationships(map_uuid_global_id, misp_obj)
#
#     return map_uuid_global_id
#
#
# if __name__ == '__main__':
#
#     # misp = PyMISP('https://127.0.0.1:8443/', 'uXgcN42b7xuL88XqK5hubwD8Q8596VrrBvkHQzB0', False)
#
#     import_objs_from_file('ail_export_c777a4d1-5f63-4fa2-86c0-07da677bdac2.json')
#
#     #Screenshot.delete_screenshot('a92d459f70c4dea8a14688f585a5e2364be8b91fbf924290ead361d9b909dcf1')
#     #Decoded.delete_decoded('d59a110ab233fe87cefaa0cf5603b047b432ee07')
#     #Pgp.pgp.delete_correlation('key', '0xA4BB02A75E6AF448')
#
#     #Item.delete_item('submitted/2020/02/10/b2485894-4325-469b-bc8f-6ad1c2dbb202.gz')
#     #Item.delete_item('archive/pastebin.com_pro/2020/02/10/K2cerjP4.gz')
