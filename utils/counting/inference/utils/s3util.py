import boto3
from dotenv import load_dotenv
from os import environ
import cv2
import logging
import json
from datetime import datetime, timedelta
import os

dotenv_path = '.env'
load_dotenv(dotenv_path)

ACCESS_KEY = environ.get('AWS_ACCESS_KEY')
SECRET_KEY = environ.get('AWS_SECRET_ACCESS_KEY')

sqs = boto3.client('sqs', 'ap-south-1', aws_access_key_id= ACCESS_KEY, aws_secret_access_key= SECRET_KEY)

def save_image(image, path):
    cv2.imwrite(path, image)
    return path

def push_data_to_sqs(record, queue_url):

    curr_time = datetime.now() + timedelta(hours=5, minutes=30)

    if not os.path.exists(f"D:/dip-data/images/ai/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}"):
        os.makedirs(f"D:/dip-data/images/ai/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}", exist_ok=True)

    if not os.path.exists(f"D:/dip-data/images/oi/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}/{curr_time.hour}"):
        os.makedirs(f"D:/dip-data/images/oi/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}/{curr_time.hour}", exist_ok=True)

    if record['originalImage'] is not None:
        record['originalImage'] = save_image(record['originalImage'], f"D:/dip-data/images/oi/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}/{curr_time.hour}/{record['imageId']}.jpg")
    if record['annotatedImage'] is not None:
        record['annotatedImage'] = save_image(record['annotatedImage'], f"D:/dip-data/images/ai/{record['cameraId']}/{curr_time.day}-{curr_time.month}-{curr_time.year}/{curr_time.hour}/{record['imageId']}.jpg")

    unique_id = str(int(datetime.now().timestamp()))

    sqs.send_message(QueueUrl = queue_url, MessageBody = json.dumps(record), MessageGroupId = 'esl-dip', MessageDeduplicationId=unique_id)