from ripikvisionpy.cloud.aws.SQSService import SQSService
from dotenv import load_dotenv
from datetime import datetime
import cv2
import logging
import os
from aggregation.multipipe import trim_multi_pipe, clear_multi_pipe_dict

load_dotenv('.env')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION_NAME')
IMAGE_STORE_PATH = os.getenv('IMAGE.LOCAL_STORE_PATH')

LAST_IMAGE_STORE_TS = 1699682737
LAST_RECORD_STORE_TS = 1699682737
IMAGE_STORE_THRESHOLD = 1

FILES_TRIMMED = 0
FILES_STORED = 0

def get_sqs_instance(client_id, material, camera_id, feature='live', queue_type='fifo'):
    # Example: sqs_esldip-local_dipcounter_ccm1_live.fifo
    sqs_queue = f'sqs_{client_id}_{material}_{camera_id}_{feature}.{queue_type}'
    print(sqs_queue)
    return SQSService(sqs_queue, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY)


def push_output_to_sqs(response, camera_id, sqs_handler):
    try:
        # print('push_output_to_sqs')
        # print(cam_to_ccm_mapping[camera_id])
        response['cameraId'] = camera_id
        response['createdAt'] = response['timestamp']

        global LAST_IMAGE_STORE_TS
        global LAST_RECORD_STORE_TS
        global FILES_TRIMMED
        global FILES_STORED

        if response['isFeedDown'] is False:  # and response['isPipePresent']
            # Store images every IMAGE_STORE_THRESHOLD gap
            if (response['createdAt'] - LAST_IMAGE_STORE_TS) > IMAGE_STORE_THRESHOLD:
                response = store_analysis_images(response)
                LAST_IMAGE_STORE_TS = response['createdAt']
            else:
                response['annotatedImage'] = None
                response['originalImage'] = None

        if response is None:
            return None

        trim_flag = False

        if camera_id in ['ccm6', 'annealing1']:
            if response['pipeCrossed'] == True:
                if trim_multi_pipe(response['pipeData']['pipeId']):
                    trim_flag = True

            if response['hasComeback'] == True:
                trim_flag=False
            
        clear_multi_pipe_dict()

        if response['pipeCrossed'] is True or response['hasComeback'] is True:
        # if response['isPipePresent'] is True:
            if trim_flag:
                if (response['createdAt'] - LAST_RECORD_STORE_TS) > IMAGE_STORE_THRESHOLD:
                    LAST_RECORD_STORE_TS = response['createdAt']
                    sqs_handler.send_json_message(response, response['cameraId'], response['imageId'])
                    FILES_STORED+=1
                else:
                    FILES_TRIMMED+=1
            else:
                sqs_handler.send_json_message(response, response['cameraId'], response['imageId'])
                FILES_STORED+=1

        # Else push single record in every second
        elif (response['createdAt'] - LAST_RECORD_STORE_TS) > IMAGE_STORE_THRESHOLD:
            LAST_RECORD_STORE_TS = response['createdAt']
            sqs_handler.send_json_message(response, response['cameraId'], response['imageId'])
            FILES_STORED+=1

        print('Files Stored: ', FILES_STORED)
        print('Files Trimmed: ', FILES_TRIMMED)

    except Exception as e:
        logging.error('Exception in push_output_to_sqs: ' + str(e), exc_info=True)


def store_analysis_images(record):
    try:
        annotated_image = record['annotatedImage']
        original_image = record['originalImage']

        oi_date = datetime.fromtimestamp(record['timestamp'])
        date_folder = oi_date.strftime('%d-%m-%Y')
        hour_folder = oi_date.strftime('%H')

        ai_image_key = f'ai/{record["cameraId"]}/{date_folder}/{hour_folder}/{record["imageId"]}.jpg'
        oi_image_key = f'oi/{record["cameraId"]}/{date_folder}/{hour_folder}/{record["imageId"]}.jpg'

        # Define the percentage by which you want to resize (e.g., 50%)
        resize_percentage = 50

        # Calculate the new dimensions based on the percentage
        new_width = int(annotated_image.shape[1] * (resize_percentage / 100))
        new_height = int(annotated_image.shape[0] * (resize_percentage / 100))

        # Resize annotated image
        annotated_image = cv2.resize(annotated_image, (new_width, new_height))
        # original_image = cv2.resize(original_image, (new_width, new_height))

        # Store images in local disk
        ai_image_link = store_image_local(IMAGE_STORE_PATH, ai_image_key, annotated_image)
        oi_image_link = store_image_local(IMAGE_STORE_PATH, oi_image_key, original_image)
        record['annotatedImage'] = ai_image_link
        record['originalImage'] = oi_image_link
        return record
    except Exception as e:
        print(e.args)
        logging.error('Exception in store_analysis() : ' + str(e))
        return None


def store_image_local(base_folder, image_path, image_file):
    complete_path = base_folder + '/' + image_path
    folder_path, file_name = os.path.split(complete_path)

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    cv2.imwrite(complete_path, image_file)
    return complete_path


if __name__ == '__main__':
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION')
    # AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    print(AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, IMAGE_STORE_PATH)