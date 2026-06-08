# myapp/tasks.py
import pickle
import time

# from celery import shared_task
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings


import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("fcm-cred.json")
firebase_admin.initialize_app(cred)


def send_fcm_notification(device_token, title, body):

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_token,
            data = {
                "body": body
            }
        )

        response = messaging.send(message)
        print('Successfully sent message:', response)
        time.sleep(3)
    except Exception as e:
        print('Error sending message:', e)
        print(f"dev-tk: {device_token}")
