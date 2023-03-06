
# awssqs connector for sesam
can be used to:
  * enqueue messages 
  * enqueue messages

[![SesamCommunity CI&CD](https://github.com/sesam-community/awssqs/actions/workflows/sesam-community-ci-cd.yml/badge.svg)](https://github.com/sesam-community/awssqs/actions/workflows/sesam-community-ci-cd.yml)
## ENV VARIABLES

| CONFIG_NAME        | DESCRIPTION           | IS_REQUIRED  |DEFAULT_VALUE|
| -------------------|---------------------|:------------:|:-----------:|
| AWS_ACCESS_KEY_ID | Access-key ID for the AWS service | yes | n/a |
| AWS_SECRET_ACCESS_KEY | Secret access-key for the AWS service | yes | n/a |
| ENDPOINT_URL | QueueUrl to use as default | no | n/a |
| ENQUEUE_CONFIG | TBD | NO | n/a |
| DEQUEUE_CONFIG | TBD | NO | n/a |
| WEBFRAMEWORK | set to 'FLASK' to use flask, otherwise it will run on cherrypy | no | n/a |
| LOG_LEVEL | LOG_LEVEL. one of [CRITICAL\|ERROR\|WARNING\|INFO\|DEBUG] | no | 'INFO' |


## ENDPOINTS

 1. `/enqueue`, methods=["POST"]

    tbd

    #### query params
    * tbd
___

 2. `/dequeue`, methods=["GET"]

    tbd

    #### query params
    * tbd
___


Example configs:

### system:
```
{
  "_id": "awssqs-service",
  "type": "system:microservice",
  "metadata": {},
  "connect_timeout": 60,
  "docker": {
    "environment": {
      "AWS_ACCESS_KEY_ID": "$SECRET(AWS_ACCESS_KEY_ID)",
      "AWS_SECRET_ACCESS_KEY": "$SECRET(AWS_SECRET_ACCESS_KEY)",
      "ENDPOINT_URL": "https://sqs.eu-west-1.amazonaws.com/636572436646/SesamTestQueue",
      "LOG_LEVEL": "DEBUG",
      "REGION_NAME": "eu-west-1"
    },
    "image": "sesamcommunity/awssqs:<myversion>",
    "port": 5000
  },
  "read_timeout": 7200
}
```

### Reading pipe
```
{
  "_id": "awssqs-message",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "awssqs-service",
    "url": "/dequeue?MAXNUMBEROFMESSAGES=10&WAITTIMESECONDS=5"
  },
  "sink": {
    "deletion_tracking": false
  },
  "transform": {
    "type": "dtl",
    "rules": {
      "default": [
        ["copy", "*"],
        ["add", "_id",
          ["string",
            ["uuid"]
          ]
        ]
      ]
    }
  },
  "pump": {
    "schedule_interval": 10
  }
}
```

### Writing pipe
```
{
  "_id": "message-awssqs-endpoint",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "message-awssqs"
  },
  "sink": {
    "type": "json",
    "system": "awssqs-service",
    "url": "/enqueue"
  },
  "transform": {
    "type": "dtl",
    "rules": {
      "default": [
        ["discard",
          ["neq", "_S._deleted", true]
        ],
        ["copy", "*"]
      ]
    }
  }
}
```