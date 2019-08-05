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

### Get item: `api/v1/get/item/default`

#### Description
Get item default info.

**Method** : `POST`

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
curl https://127.0.0.1:7000/api/v1/get/item/default --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
  }
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
```json
  {"status": "error", "reason": "Mandatory parameter(s) not provided"}
```
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```




### Get item content: `api/v1/get/item/content`

#### Description
Get a specific item content.

**Method** : `POST`

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
curl https://127.0.0.1:7000/api/v1/get/item/content --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
  }
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
```json
  {"status": "error", "reason": "Mandatory parameter(s) not provided"}
```
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```



### Get item content: `api/v1/get/item/tag`

#### Description
Get all tags from an item.

**Method** : `POST`

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
curl https://127.0.0.1:7000/api/v1/get/item/tag --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
  }
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
```json
  {"status": "error", "reason": "Mandatory parameter(s) not provided"}
```
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```



### Advanced Get item: `api/v1/get/item`

#### Description
Get item. Filter requested field.

**Method** : `POST`

#### Parameters
- `id`
  - item id
  - *str - relative item path*
  - mandatory
- `date`
  - get item date
  - *boolean*
  - default: `true`
- `tags`
  - get item tags
  - *boolean*
  - default: `true`
- `content`
  - get item content
  - *boolean*
  - default: `false`
- `size`
  - get item size
  - *boolean*
  - default: `false`
- `lines`
  - get item lines info
  - *boolean*
  - default: `false`

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
- `size`
  - item size (Kb)
  - *int*
- `lines`
  - item lines info
  - *{}*
      - `max_length`
        -  line max length line
        - *int*
      - `nb`
        - nb lines item
        - *int*


#### Example
```
curl https://127.0.0.1:7000/api/v1/get/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
{
  "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
  "content": true,
  "lines_info": true,
  "tags": true,
  "size": true
}
```

#### Expected Success Response
**HTTP Status Code** : `200`
```json
  {
    "content": "dsvcdsvcdsc vvvv",
    "date": "20190726",
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "lines": {
      "max_length": 19,
      "nb": 1
    },
    "size": 0.03,
    "tags": [
      "misp-galaxy:stealer=\"Vidar\"",
      "infoleak:submission=\"manual\""
    ]
  }
```

#### Expected Fail Response
**HTTP Status Code** : `400`
```json
  {"status": "error", "reason": "Mandatory parameter(s) not provided"}
```
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```





### add item tags: `api/v1/add/item/tag`

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
curl https://127.0.0.1:7000/api/v1/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
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

```json
  {"status": "error", "reason": "Item id not found"}
  {"status": "error", "reason": "Tags or Galaxy not specified"}
  {"status": "error", "reason": "Tags or Galaxy not enabled"}
```




### Delete item tags: `api/v1/delete/item/tag`

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
curl https://127.0.0.1:7000/api/v1/delete/item/tag --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X DELETE
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

```json
  {"status": "error", "reason": "Item id not found"}
  {"status": "error", "reason": "No Tag(s) specified"}
```






## Tag management


### Get all AIL tags: `api/v1/get/tag/all`

#### Description
Get all tags used in AIL.

**Method** : `GET`

#### JSON response
- `tags`
  - list of tag
  - *list*
#### Example
```
curl https://127.0.0.1:7000/api/v1/get/tag/all --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"
```

#### Expected Success Response
**HTTP Status Code** : `200`
```json
  {
    "tags": [
      "misp-galaxy:backdoor=\"Rosenbridge\"",
      "infoleak:automatic-detection=\"pgp-private-key\"",
      "infoleak:automatic-detection=\"pgp-signature\"",
      "infoleak:automatic-detection=\"base64\"",
      "infoleak:automatic-detection=\"encrypted-private-key\"",
      "infoleak:submission=\"crawler\"",
      "infoleak:automatic-detection=\"binary\"",
      "infoleak:automatic-detection=\"pgp-public-key-block\"",
      "infoleak:automatic-detection=\"hexadecimal\"",
      "infoleak:analyst-detection=\"private-key\"",
      "infoleak:submission=\"manual\"",
      "infoleak:automatic-detection=\"private-ssh-key\"",
      "infoleak:automatic-detection=\"iban\"",
      "infoleak:automatic-detection=\"pgp-message\"",
      "infoleak:automatic-detection=\"certificate\"",
      "infoleak:automatic-detection=\"credential\"",
      "infoleak:automatic-detection=\"cve\"",
      "infoleak:automatic-detection=\"google-api-key\"",
      "infoleak:automatic-detection=\"phone-number\"",
      "infoleak:automatic-detection=\"rsa-private-key\"",
      "misp-galaxy:backdoor=\"SLUB\"",
      "infoleak:automatic-detection=\"credit-card\"",
      "misp-galaxy:stealer=\"Vidar\"",
      "infoleak:automatic-detection=\"private-key\"",
      "infoleak:automatic-detection=\"api-key\"",
      "infoleak:automatic-detection=\"mail\""
    ]
  }
```




### Get tag metadata: `api/v1/get/tag/metadata`

#### Description
Get tag metadata.

**Method** : `POST`

#### Parameters
- `tag`
  - tag name
  - *str*
  - mandatory

#### JSON response
- `tag`
  - tag name
  - *str*
- `first_seen`
  - date: first seen
  - *str - YYMMDD*
- `last_seen`
  - date: first seen
  - *str - YYMMDD*
#### Example
```
curl https://127.0.0.1:7000/api/v1/get/tag/metadata --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "tag": "infoleak:submission=\"manual\""
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`
```json
  {
    "first_seen": "20190605",
    "last_seen": "20190726",
    "tag": "infoleak:submission=\"manual\""
  }
```

#### Expected Fail Response
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Tag not found"}
```






## Import management



### Import item (currently: text only): `api/v1/import/item`

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
curl https://127.0.0.1:7000/api/v1/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
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

```json
  {"status": "error", "reason": "Malformed JSON"}
  {"status": "error", "reason": "No text supplied"}
  {"status": "error", "reason": "Tags or Galaxy not enabled"}
  {"status": "error", "reason": "Size exceeds default"}
```





### GET Import item info: `api/v1/get/import/item/`

#### Description

Get import status and all items imported by uuid

**Method** : `POST`

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
curl -k https://127.0.0.1:7000/api/v1/get/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "uuid": "0c3d7b34-936e-4f01-9cdf-2070184b6016"
  }
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

```json
  {"status": "error", "reason": "Invalid uuid"}
  {"status": "error", "reason": "Unknown uuid"}
```








# FUTURE endpoints

### Text search by daterange
##### ``api/search/textIndexer/item`` POST

### Get tagged items by daterange
##### ``api/search/tag/item`` POST

### Submit a domain to crawl
##### ``api/add/crawler/domain`` POST

### Create a term/set/regex tracker
##### ``api/add/termTracker/`` POST

### Get tracker items list
##### ``api/get/termTracker/item`` POST

-----

### Check if a tor/regular domain have been crawled
##### ``api/get/crawler/domain/`` POST

### Check if a tor/regular domain have been crawled
##### ``api/get/crawler/domain/metadata/ <domain><port>`` POST

### Get domain tags
##### ``api/get/crawler/domain/tag/ <domain><port>`` POST

### Get domain history
##### ``api/get/crawler/domain/history/ <domain><port>`` POST

### Get domain list of items
##### ``api/get/crawler/domain/item/ <domain><port>`` POST

-----

### Create auto-crawlers
##### ``api/add/crawler/autoCrawler/`` POST

-----

### get item by mime type/ decoded type
##### ``api/get/decoded`` POST

### Check if a decoded item exists (via sha1)
##### ``api/get/decoded/exist/<sha1>`` POST

### Get decoded item metadata
### Check if a decoded item exists (via sha1)
##### ``api/get/decoded/metadata/<sha1>`` POST

### Get decoded item correlation (1 depth)
##### ``api/get/decoded/metadata/<sha1>`` POST

-----


-----
##### ``api/get/cryptocurrency`` POST

### Check if a cryptocurrency address (bitcoin, ..) exists
##### ``api/get/cryptocurrency/exist/<bitcoin_address>`` POST

### Get cryptocurrency address metadata
##### ``api/get/cryptocurrency/metadata/<bitcoin_address>`` POST

-----

### Item correlation (1 depth)
##### ``api/get/item/correlation/`` POST

### Create MISP event from item
##### ``api/export/item/misp`` POST

### Create TheHive case from item
##### ``api/export/item/thehive`` POST
