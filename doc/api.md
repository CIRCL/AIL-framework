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

### Get item: `api/v1/get/item/default`<a name="get_item_default"></a>

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




### Get item content: `api/v1/get/item/content`<a name="get_item_content"></a>

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



### Get item content: `api/v1/get/item/tag`<a name="get_item_tag"></a>

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



### Advanced Get item: `api/v1/get/item`<a name="get_item"></a>

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
- `cryptocurrency`
  - `bitcoin`
    - get item bitcoin adress
    - *boolean*
    - default: `false`
- `pgp`
  - `key`
    - get item pgp key
    - *boolean*
    - default: `false`
  - `mail`
    - get item pgp mail
    - *boolean*
    - default: `false`
  - `name`
    - get item pgp name
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
- `cryptocurrency`
  - `bitcoin`
    - item bitcoin adress
    - *list*
- `pgp`
  - `key`
    - item pgp keys
    - *list*
  - `mail`
    - item pgp mails
    - *list*
  - `name`
    - item pgp name
    - *list*


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
    "cryptocurrency": {
      "bitcoin": [
        "132M1aGTGodHkQNh1augLeMjEXH51wgoCc"
      ]
    },
    "date": "20190726",
    "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
    "lines": {
      "max_length": 19,
      "nb": 1
    },
    "pgp": {
      "key": [
        "0x5180D21F4C20F975"
      ],
      "mail": [
        "mail@test.test"
      ],
      "name": [
        "user_test"
      ]
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





### Add item tags: `api/v1/add/item/tag`<a name="add_item_tag"></a>

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




### Delete item tags: `api/v1/delete/item/tag`<a name="delete_item_tag"></a>

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


### Get all AIL tags: `api/v1/get/tag/all`<a name="get_tag_all"></a>

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




### Get tag metadata: `api/v1/get/tag/metadata`<a name="get_tag_metadata"></a>

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
  - *str - YYYYMMDD*
- `last_seen`
  - date: last seen
  - *str - YYYYMMDD*
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




## Cryptocurrency



### Get bitcoin metadata: `api/v1/get/cryptocurrency/bitcoin/metadata`<a name="get_cryptocurrency_bitcoin_metadata"></a>

#### Description
Get all metdata from a bitcoin address.

**Method** : `POST`

#### Parameters
- `bitcoin`
  - bitcoin address
  - *str*
  - mandatory

#### JSON response
- `bitcoin`
  - bitcoin address
  - *str*
- `first_seen`
  - date: first seen
  - *str - YYYYMMDD*
- `last_seen`
  - date: last seen
  - *str - YYYYMMDD*
#### Example
```
curl https://127.0.0.1:7000/api/v1/get/cryptocurrency/bitcoin/metadata --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "bitcoin": "3DZfm5TQaJKcJm9PsuaWmSz9XmHMLxVv3y"
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`
```json
  {
    "bitcoin": "3DZfm5TQaJKcJm9PsuaWmSz9XmHMLxVv3y",
    "first_seen": "20190605",
    "last_seen": "20190726"
  }
```

#### Expected Fail Response
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```



### Get bitcoin metadata: `api/v1/get/cryptocurrency/bitcoin/item`<a name="get_cryptocurrency_bitcoin_item"></a>

#### Description
Get all items related to a bitcoin address.

**Method** : `POST`

#### Parameters
- `bitcoin`
  - bitcoin address
  - *str*
  - mandatory

#### JSON response
- `bitcoin`
  - bitcoin address
  - *str*
- `items`
  - list of item id
  - *list*
#### Example
```
curl https://127.0.0.1:7000/api/v1/get/cryptocurrency/bitcoin/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "bitcoin": "3DZfm5TQaJKcJm9PsuaWmSz9XmHMLxVv3y"
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`
```json
  {
    "bitcoin": "3DZfm5TQaJKcJm9PsuaWmSz9XmHMLxVv3y",
    "items": [
      "archive/2019/08/26/test_bitcoin001",
      "archive/2019/08/26/test_bitcoin002",
      "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
    ]
  }
```

#### Expected Fail Response
**HTTP Status Code** : `404`
```json
  {"status": "error", "reason": "Item not found"}
```







## Tracker



### Add term tracker: `api/v1/add/tracker`<a name="add_tracker"></a>

#### Description
Create a new tracker (word, set, regex).

You need to use a regex if you want to use one of the following special characters [<>~!?@#$%^&*|()_-+={}\":;,.\'\n\r\t]/\\


**Method** : `POST`

#### Parameters
- `term`
  - term to add
  - *str - word(s)*
  - mandatory
- `nb_words`
  - number of words in set
  - *int*
  - default: `1`
- `type`
  - term type
  - *str*
  - mandatory: `word`, `set`, `regex`
- `tags`
  - list of tags
  - *list*
  - default: `[]`
- `mails`
  - list of mails to notify
  - *list*
  - default: `[]`
- `level`
  - tracker visibility
  - *int - 0: user only, 1: all users*
  - default: `1`
- `description`
  - tracker description
  - *str*

#### JSON response
- `uuid`
  - import uuid
  - *uuid4*

#### Example
```
curl https://127.0.0.1:7000/api/v1/add/tracker --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "term": "test test2 test3",
    "type": "set",
    "nb_words": 2,
    "tags": [
      "mytags",
      "othertags"
    ],
    "mails": [
      "mail@mail.test",
      "othermail@mail.test"
    ],
    "level": 1
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "uuid": "6a16b06e-38e5-41e1-904d-3960610647e8"
  }
```

#### Expected Fail Response
**HTTP Status Code** : 400

```json
  {"status": "error", "reason": "Term not provided"}
  {"status": "error", "reason": "Term type not provided"}
  {"status": "error", "reason": "special character not allowed", "message": "Please use a regex or remove all special characters"}
  {"status": "error", "reason": "Incorrect type"}
```
**HTTP Status Code** : 409

```json
  {"status": "error", "reason": "Term already tracked"}
```



### Delete term tracker: `api/v1/delete/tracker`<a name="delete_tracker"></a>

#### Description
Delete a tracker

**Method** : `DELETE`

#### Parameters
- `uuid`
  - tracked term uuid
  - *uuid4*
  - mandatory

#### JSON response
- `uuid`
  - deleted uuid
  - *uuid4*

#### Example
```
curl https://127.0.0.1:7000/api/v1/delete/tracker --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "uuid": "6a16b06e-38e5-41e1-904d-3960610647e8"
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "uuid": "6a16b06e-38e5-41e1-904d-3960610647e8"
  }
```

#### Expected Fail Response
**HTTP Status Code** : `400`

```json
  {"status": "error", "reason": "Invalid uuid"}

```

**HTTP Status Code** : `404`

```json
  ({"status": "error", "reason": "Unknown uuid"}

```


### Delete term tracker: `api/v1/get/tracker/item`<a name="get_tracker_item"></a>

#### Description
Get tracked items by date-range

**Method** : `POST`

#### Parameters
- `uuid`
  - tracked term uuid
  - *uuid4*
  - mandatory
- `date_from`
  - date from
  - *str - YYMMDD*
  - default: last tracked items date
- `date_to`
  - date to
  - *str - YYMMDD*
  - default: `None`

#### JSON response
- `uuid`
  - term uuid
  - *uuid4*
- `date_from`
  - date from
  - *str - YYMMDD*
- `date_to`
  - date to
  - *str - YYMMDD*
- `items`
  - list of item id
  - *list*

#### Example
```
curl https://127.0.0.1:7000/api/v1/get/tracker/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "uuid": "6a16b06e-38e5-41e1-904d-3960610647e8",
    "date_from": "20190823",
    "date_to": "20190829",
    "items": [
      {
        "id": "submitted/2019/08/25/4f929998-3921-4be3-b448-be3bf1722d6b.gz",
        "date": 20190825,
        "tags": [
          "infoleak:automatic-detection=\"credential\"",
          "mytags",
          "othertags",
        ]
      }
    ]
  }
```

**HTTP Status Code** : `400`

```json
  {"status": "error", "reason": "Invalid uuid"}

```

**HTTP Status Code** : `404`

```json
  ({"status": "error", "reason": "Unknown uuid"}

```



## Domain


### Get min domain metadata: `api/v1/get/crawled/domain/list`<a name="get_crawled_domain_list"></a>

#### Description
Get crawled domain by date-range and status (default status = *UP*)

**Method** : `POST`

#### Parameters
- `domain_type`
  - domain type: *onion* or *regular*
  - *str*
  - default: *regular*
- `date_from`
  - date from
  - *str - YYYYMMDD*
  - mandatory
- `date_to`
  - date to
  - *str - YYYYMMDD*
  - mandatory

#### JSON response
- `domain_type`
  - domain type: *onion* or *regular*
  - *str*
- `date_from`
  - date from
  - *str - YYYYMMDD*
- `date_to`
  - date to
  - *str - YYYYMMDD*
- `domains`
  - list of domains
  - *list - list of domains*

#### Example
```
curl https://127.0.0.1:7000/api/v1/get/crawled/domain/list --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "date_from": "20191001",
    "date_to": "20191222",
    "domain_type": "onion"
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "date_from": "20191001",
    "date_to": "20191222",
    "domain_status": "UP",
    "domain_type": "onion",
    "domains": [
      "2222222222222222.onion"
    ]
  }
```




### Get min domain metadata: `api/v1/get/domain/status/minimal`<a name="get_domain_status_minimal"></a>

#### Description
Get min domain metadata

**Method** : `POST`

#### Parameters
- `domain`
  - domain name
  - *str*
  - mandatory

#### JSON response
- `domain`
  - domain
  - *str*
- `first_seen`
  - domain first up time
  - *epoch*
- `last_seen`
  - domain last up time
  - *epoch*

#### Example
```
curl https://127.0.0.1:7000/api/v1/get/domain/status/minimal --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST
```

#### input.json Example
```json
  {
    "domain": "2222222222222222.onion",
  }
```

#### Expected Success Response
**HTTP Status Code** : `200`

```json
  {
    "domain": "2222222222222222.onion",
    "first_seen": 1571314000,
    "last_seen": 1571314000
  }
```

**HTTP Status Code** : `404`

```json
  ({"status": "error", "reason": "Domain not found"}

```



## Import management



### Import item (currently: text only): `api/v1/import/item`<a name="import_item"></a>

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





### GET Import item info: `api/v1/get/import/item/`<a name="get_import_item"></a>

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

<details>
<summary>Endpoints</summary>

### Submit a domain to crawl TODO
##### ``api/add/crawler/task`` POST

### Create a term/set/regex/yara tracker
##### ``api/add/tracker/`` POST

### Get tracker
##### ``api/get/tracker`` POST

-----



### Get domain tags
##### ``api/get/domain/tags/<domain>`` POST

### Get domain history
##### ``api/get/domain/history/<domain>`` POST

-----

### Get decoded item metadata
### Check if a decoded item exists (via sha1)
##### ``api/get/decoded/metadata/<sha1>`` POST

-----


-----
##### ``api/get/cryptocurrency`` POST

### Check if a cryptocurrency address (bitcoin, ..) exists
##### ``api/get/cryptocurrency/<bitcoin_address>`` POST

### Get cryptocurrency address metadata
##### ``api/get/cryptocurrency/metadata/<coin_address>`` POST

-----

### Object correlation (1 depth)
##### ``api/get/correlation/`` POST

### Create MISP event from object
##### ``api/export/misp`` POST

</details>

-----

