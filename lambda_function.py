import json
import requests
import boto3

def check_message_channel_type(message):
    # this checks if the message is private chat or in a group
    if "chat" in message:
        if "type" in message["chat"]:
            if message["chat"]["type"] == "private":
                return "private"
            elif message["chat"]["type"] == "supergroup":
                return "supergroup"

    return None

def get_message_from_dynamodb(id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('messages')

    response = table.get_item(
        Key={
            'id': str(id)
        }
    )

    return response.get("Item", None)

def add_message_to_dynamodb(id, message):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('messages')

    table.put_item(
        Item={
            'id': str(id),
            'message': message
        }
    )

def lambda_handler(event, context):
    data = json.loads(event["body"])

    message_type = check_message_channel_type(data["message"])

    # admins_group_id = "-1002433012292"
    admins_group_id = "<YOUR_GROUP_ID>"
    token = "<YOUR_BOT_TOKEN>"

    if not message_type:
        return {
            "statusCode": 200,
            "body": json.dumps(data)
        }

    if message_type == "private":
        chat_id = data["message"]["chat"]["id"]
        name = data["message"]["chat"]["first_name"]
        message = data["message"]["text"]

        reply_message_to_group = f"Message from {name}: \n\n{message}"

        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={
                              "chat_id": admins_group_id,
                              "text": reply_message_to_group
                          }
                          )

        message_id_in_group = r.json()["result"]["message_id"]
        # }
        add_message_to_dynamodb(message_id_in_group, {
                                "chat_id": chat_id,
                                "message": message
                                })


    elif message_type == "supergroup":
        if "reply_to_message" not in data["message"]:
            return {
                "statusCode": 200,
                "body": json.dumps(data)
            }

        reply_message_id = data["message"]["reply_to_message"]["message_id"]

        message = get_message_from_dynamodb(reply_message_id)

        if not message:
            return {
                "statusCode": 200,
                "body": json.dumps(data)
            }

        message = message["message"]

        chat_id = message["chat_id"]
        message = data["message"]["text"]

        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={
                              "chat_id": chat_id,
                              "text": message
                          }
                          )

        return {
            "statusCode": 200,
            "body": json.dumps(data)
        }

    # return 200
    return {
        "statusCode": 200,
        "body": json.dumps(data)
    }
