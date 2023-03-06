import json
import boto3
import os
import datetime
from flask import Flask, request, Response, abort, Request
from sesamutils import sesam_logger
from sesamutils.flask import serve

app = Flask(__name__)

logger = sesam_logger("amazonsqs-service", app=app)

ENDPOINT_URL=os.environ.get("ENDPOINT_URL")
REGION_NAME=os.environ.get("REGION_NAME")
AWS_ACCESS_KEY_ID=os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.environ.get("AWS_SECRET_ACCESS_KEY")

logger.debug(f"REGION_NAME={REGION_NAME}, ENDPOINT_URL:{ENDPOINT_URL}")

def _get_converted_or_none(v):
    if not v:
        return None
    else:
        return int(v)

ENQUEUE_CONFIG=json.loads(os.environ.get("ENQUEUE_CONFIG","{}"))
DEQUEUE_CONFIG=json.loads(os.environ.get("DEQUEUE_CONFIG","{}"))

PORT=int(os.environ.get("PORT",5000))

def unsesamify(input):
    entities = []
    if isinstance(input, list):
        for e in input:
            entities.append(unsesamify(e))
        return entities
    else:
        sesam_fields = []
        for p in input.keys():
            if p.startswith("_"):
                sesam_fields.append(p)
        for p in sesam_fields:
            del(input[p])

        return input

def get_client():
    return boto3.client(service_name='sqs',region_name=REGION_NAME,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

@app.route('/enqueue', methods=["POST"])
def enqueue():
    try:        
        data = request.get_json()
        sqs = get_client()        
        QueueUrl=request.args.get("QUEUEURL",ENDPOINT_URL)
        DelaySeconds=request.args.get("DELAYSECONDS") or ENQUEUE_CONFIG.get("DELAYSECONDS")
        MessageDeduplicationId_property=request.args.get("MESSAGEDEDUPLICATIONID_PROPERTY") or ENQUEUE_CONFIG.get("MESSAGEDEDUPLICATIONID_PROPERTY")
        MessageGroupId=request.args.get("MESSAGEGROUPID") or ENQUEUE_CONFIG.get("MESSAGEGROUPID")
        is_success=True
        # Send message to SQS queue
        if isinstance(data, dict):
            data = [data]
        elif isinstance(data, list):
            pass
        else:
            abort(400,"only application/json is supported")
        
        logger.debug(f"QueueUrl={QueueUrl}")
        for d in data:
            params={"DelaySeconds":int(DelaySeconds) if DelaySeconds else None, "MessageGroupId":MessageGroupId}
            params["MessageDeduplicationId"]=d.get(MessageDeduplicationId_property)
            not_none_params = {k:v for k, v in params.items() if v is not None}
            response = sqs.send_message(
                QueueUrl=QueueUrl,
                MessageBody=json.dumps(d),
                **not_none_params)
        return Response(response="OK", content_type="text/plain", status=200)
    except Exception as err:
        logger.exception(err)
        return Response(str(err), mimetype='plain/text', status=500)

@app.route('/dequeue', methods=["GET"])
def dequeue():
    try:  
        sqs=get_client()      
        QueueUrl=request.args.get("ENDPOINT_URL",ENDPOINT_URL)
        
        params={
            "MaxNumberOfMessages":request.args.get("MAXNUMBEROFMESSAGES") or DEQUEUE_CONFIG.get("MAXNUMBEROFMESSAGES"),
            "WaitTimeSeconds":request.args.get("WAITTIMESECONDS") or DEQUEUE_CONFIG.get("WAITTIMESECONDS"),
            "VisibilityTimeout":request.args.get("VISIBILITYTIMEOUT") or DEQUEUE_CONFIG.get("DEQUEUE_VISIBILITYTIMEOUT"),
            "ReceiveRequestAttemptId":None
        }
        try:
            not_none_params = {k:int(v) for k, v in params.items() if v is not None}
        except Exception as err:
            logger.exception(err)
            return Response(str(err), mimetype='plain/text', status=400)

        logger.debug(f"QueueUrl={QueueUrl}")

        data = []
        while True:
            response = sqs.receive_message(
                QueueUrl=QueueUrl,
                **not_none_params
            )        
            for message in response.get('Messages',[]):
                msg_body = message["Body"]
                data.append(json.loads(msg_body))
                receipt_handle = message['ReceiptHandle']

                # Delete received message from queue
                sqs.delete_message(
                    QueueUrl=QueueUrl,
                    ReceiptHandle=receipt_handle
                )
            else:
                break

        return Response(response=json.dumps(data), content_type="application/json", status=200)
    except Exception as err:
        logger.exception(err)
        return Response(str(err), mimetype='plain/text', status=500)


if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    if os.environ.get("WEBFRAMEWORK", "") == "FLASK":
        app.run(debug=True, host='0.0.0.0', port=PORT)
    else:
        serve(app, port=PORT)

