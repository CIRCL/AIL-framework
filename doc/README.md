#  API DOCUMENTATION

## General

### Automation key

The authentication of the automation is performed via a secure key available in the AIL UI interface. Make sure you keep that key secret. It gives access to the entire database! The API key is available in the ``Server Management`` menu under ``My Profile``.

The authorization is performed by using the following header:

~~~~
Authorization: YOUR_API_KEY
~~~~
### Accept and Content-Type headers

When submitting data in a POST, PUT or DELETE operation you need to specify in what content-type you encoded the payload. This is done by setting the below Content-Type headers:

~~~~
Content-Type: application/json
~~~~

Example:

~~~~
curl --header "Authorization: YOUR_API_KEY" --header "Content-Type: application/json" https://AIL_URL/
~~~~

## Item management

### Get item: `api/get/item/info/<path:item_id>`

#### Description
Get a specific item information.

**Method** : `GET`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory

#### JSON response
- `content`
  - item content
  - *str*
- `id`
  - item id
  - *str*
- `date`
  - item date
  - *str - YYMMDD*
- `tags`
  - item tags list
  - *list*

#### Example
```
curl https://127.0.0.1:7000/api/get/item/info/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "content": "item content test",
    "date": "20190726",
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags":
      [
        "misp-galaxy:backdoor=\"Rosenbridge\"",
        "infoleak:automatic-detection=\"pgp-message\"",
        "infoleak:automatic-detection=\"encrypted-private-key\"",
        "infoleak:submission=\"manual\"",
        "misp-galaxy:backdoor=\"SLUB\""
      ]
  }
```

#### Expected Fail Response

**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Item not found'}
```




### Get item content: `api/get/item/content/<path:item_id>`

#### Description
Get a specific item content.

**Method** : `GET`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory

#### JSON response
- `content`
  - item content
  - *str*
- `id`
  - item id
  - *str*

#### Example
```
curl https://127.0.0.1:7000/api/get/item/content/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "content": "item content test",
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
  }
```

#### Expected Fail Response

**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Item not found'}
```



### Get item content: `api/get/item/tag/<path:item_id>`

#### Description
Get all tags from an item.

**Method** : `GET`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory

#### JSON response
- `content`
  - item content
  - *str*
- `tags`
  - item tags list
  - *list*

#### Example
```
curl https://127.0.0.1:7000/api/get/item/tag/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags":
      [
        "misp-galaxy:backdoor=\"Rosenbridge\"",
        "infoleak:automatic-detection=\"pgp-message\"",
        "infoleak:automatic-detection=\"encrypted-private-key\"",
        "infoleak:submission=\"manual\"",
        "misp-galaxy:backdoor=\"SLUB\""
      ]
  }
```

#### Expected Fail Response

**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Item not found'}
```



### add item tags: `api/add/item/tag`

#### Description
Add tags to an item.

**Method** : `POST`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory
- `tags`
  - list of tags
  - *list*
  - default: `[]`
- `galaxy`
  - list of galaxy
  - *list*
  - default: `[]`

#### JSON response
- `id`
  - item id
  - *str - relative item path*
- `tags`
  - list of item tags added
  - *list*

#### Example
```
curl https://127.0.0.1:7000/api/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags": [
      "infoleak:analyst-detection=\"private-key\"",
      "infoleak:analyst-detection=\"api-key\""
    ],
    "galaxy": [
      "misp-galaxy:stealer=\"Vidar\""
    ]
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags": [
      "infoleak:analyst-detection=\"private-key\"",
      "infoleak:analyst-detection=\"api-key\"",
      "misp-galaxy:stealer=\"Vidar\""
    ]
  }
```

#### Expected Fail Response
**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Item id not found'}
  {'status': 'error', 'reason': 'Tags or Galaxy not specified'}
  {'status': 'error', 'reason': 'Tags or Galaxy not enabled'}
```




### Delete item tags: `api/delete/item/tag`

#### Description
Delete tags from an item.

**Method** : `DELETE`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory
- `tags`
  - list of tags
  - *list*
  - default: `[]`

#### JSON response
- `id`
  - item id
  - *str - relative item path*
- `tags`
  - list of item tags deleted
  - *list*

#### Example
```
curl https://127.0.0.1:7000/api/delete/item/tag --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X DELETE
```

#### input.json Example
```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags": [
      "infoleak:analyst-detection=\"private-key\"",
      "infoleak:analyst-detection=\"api-key\"",
      "misp-galaxy:stealer=\"Vidar\""
    ]
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "tags": [
      "infoleak:analyst-detection=\"private-key\"",
      "infoleak:analyst-detection=\"api-key\"",
      "misp-galaxy:stealer=\"Vidar\""
    ]
  }
```

#### Expected Fail Response
**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Item id not found'}
  {'status': 'error', 'reason': 'No Tag(s) specified'}
```







## Import management



### Import item (currently: text only): `api/import/item`

#### Description
Allows users to import new items. asynchronous function.

**Method** : `POST`

#### Parameters
- `type`
  - import type
  - *str*
  - default: `text`
- `text`
  - text to import
  - *str*
  - mandatory if type = text
- `default_tags`
  - add default import tag
  - *boolean*
  - default: True
- `tags`
  - list of tags
  - *list*
  - default: `[]`
- `galaxy`
  - list of galaxy
  - *list*
  - default: `[]`

#### JSON response
- `uuid`
  - import uuid
  - *uuid4*

#### Example
```
curl https://127.0.0.1:7000/api/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "type": "text",
    "tags": [
      "infoleak:analyst-detection=\"private-key\""
    ],
    "text": "text to import"
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "uuid": "0c3d7b34-936e-4f01-9cdf-2070184b6016"
  }
```

#### Expected Fail Response
**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Malformed JSON'}
  {'status': 'error', 'reason': 'No text supplied'}
  {'status': 'error', 'reason': 'Tags or Galaxy not enabled'}
  {'status': 'error', 'reason': 'Size exceeds default'}
```





### GET Import item info: `api/import/item/<uuid4>`

#### Description

Get import status and all items imported by uuid

**Method** : `GET`

#### Parameters

- `uuid`
  - import uuid
  - *uuid4*
  - mandatory

#### JSON response

- `status`
  - import status
  - *str*
  - values: `in queue`, `in progress`, `imported`
- `items`
  - list of imported items id
  - *list*
  - The full list of imported items is not complete until `status` = `"imported"`

#### Example

```
curl -k https://127.0.0.1:7000/api/import/item/b20a69f1-99ad-4cb3-b212-7ce24b763b50 --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"
```

#### Expected Success Response

**HTTP Status Code** : `200`

```json
  {
    "items": [
      "submitted/2019/07/26/b20a69f1-99ad-4cb3-b212-7ce24b763b50.gz"
    ],
    "status": "imported"
  }
```

#### Expected Fail Response

**HTTP Status Code** : `400`

```
  {'status': 'error', 'reason': 'Invalid uuid'}
  {'status': 'error', 'reason': 'Unknow uuid'}
```
