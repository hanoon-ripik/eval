import os
import re
import json
from urllib.parse import urlparse
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()
DEFAULT_AWS_CREDENTIALS = {
    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "region": "ap-south-1"
}

def parse_s3_url(s3_url):
    """
    Parse S3 URL to extract bucket, key, and region.
    
    Supports formats:
    - https://bucket-name.s3.region.amazonaws.com/key/path
    - https://s3.region.amazonaws.com/bucket-name/key/path
    - s3://bucket-name/key/path
    
    Args:
        s3_url (str): S3 URL to parse
        
    Returns:
        tuple: (bucket, key, region) or (None, None, None) if parsing fails
    """
    try:
        parsed = urlparse(s3_url)
        
        if parsed.scheme == 's3':
            # s3://bucket-name/key/path format
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            region = "us-east-1"  # Default region for s3:// URLs
            return bucket, key, region
            
        elif parsed.scheme in ['http', 'https']:
            hostname = parsed.hostname
            
            if '.s3.' in hostname:
                # https://bucket-name.s3.region.amazonaws.com/key/path format
                bucket = hostname.split('.s3.')[0]
                region_match = re.search(r'\.s3\.([^.]+)\.amazonaws\.com', hostname)
                region = region_match.group(1) if region_match else "us-east-1"
                key = parsed.path.lstrip('/')
                return bucket, key, region
                
            elif hostname.startswith('s3.') or hostname.startswith('s3-'):
                # https://s3.region.amazonaws.com/bucket-name/key/path format
                path_parts = parsed.path.lstrip('/').split('/', 1)
                if len(path_parts) >= 2:
                    bucket = path_parts[0]
                    key = path_parts[1]
                    region_match = re.search(r's3[.-]([^.]+)\.amazonaws\.com', hostname)
                    region = region_match.group(1) if region_match else "us-east-1"
                    return bucket, key, region
        
        print(f"Warning: Could not parse S3 URL format: {s3_url}")
        return None, None, None
        
    except Exception as e:
        print(f"Error parsing S3 URL: {e}")
        return None, None, None

def get_aws_credentials():
    """
    Always use default AWS credentials.
    
    Returns:
        dict: AWS credentials
    """
    return DEFAULT_AWS_CREDENTIALS.copy()

def download_from_s3_with_custom_name(bucket, object_key, credentials, output_dir="./", custom_filename=None):
    """
    Download a file from AWS S3 using proper AWS authentication with custom filename.
    
    Args:
        bucket (str): S3 bucket name
        object_key (str): S3 object key
        credentials (dict): AWS credentials
        output_dir (str): Directory to save the downloaded file
        custom_filename (str): Custom filename for the downloaded file
    
    Returns:
        str: Path to downloaded file or None if failed
    """
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
            region_name=credentials["region"]
        )
        
        # Prepare output path
        if custom_filename:
            filename = custom_filename
        else:
            filename = os.path.basename(object_key)
            if not filename:
                filename = "downloaded_file"
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        print(f"Downloading from S3: s3://{bucket}/{object_key}")
        print(f"Saving to: {output_path}")
        
        # First, check if object exists and we have access
        try:
            s3_client.head_object(Bucket=bucket, Key=object_key)
            print("✓ Object exists and is accessible")
        except ClientError as e:
            if e.response['Error']['Code'] == '403':
                print("✗ Access denied - checking credentials and permissions...")
                return None
            elif e.response['Error']['Code'] == '404':
                print("✗ Object not found")
                return None
            else:
                raise e
        
        # Download the file
        s3_client.download_file(bucket, object_key, output_path)
        
        print(f"Download completed successfully: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        return output_path
        
    except Exception as e:
        print(f"Error downloading from S3: {e}")
        return None

def process_big_rock_data():
    """
    Process big rock JSON files and create clean.json with downloaded images.
    """
    print("Processing Big Rock data and downloading images...")
    
    # Read the JSON files
    try:
        with open('ultratech-coal-sizing.history_false.json', 'r') as f:
            false_data = json.load(f)
        print(f"Found {len(false_data)} items in history_false.json")
    except FileNotFoundError:
        print("Error: ultratech-coal-sizing.history_false.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing history_false.json: {e}")
        return
    
    try:
        with open('ultratech-coal-sizing.history_true.json', 'r') as f:
            true_data = json.load(f)
        print(f"Found {len(true_data)} items in history_true.json")
    except FileNotFoundError:
        print("Error: ultratech-coal-sizing.history_true.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing history_true.json: {e}")
        return
    
    # Limit the data to process
    false_data = false_data[:120]  # Limit to 120 false items
    true_data = true_data[:30]     # Limit to 30 true items
    
    # Get AWS credentials
    credentials = get_aws_credentials()
    
    # Create clean data structure
    clean_data = []
    
    # Create downloads directories
    os.makedirs("./downloads/original/true", exist_ok=True)
    os.makedirs("./downloads/original/false", exist_ok=True)
    os.makedirs("./downloads/annotated/true", exist_ok=True)
    os.makedirs("./downloads/annotated/false", exist_ok=True)
    
    id_counter = 1
    
    # Process false data (bigParticlePresent = false)
    print(f"\nProcessing {len(false_data)} items from false data (limited to 120)...")
    for idx, item in enumerate(false_data):
        print(f"\nProcessing false item {idx+1}/{len(false_data)} -> ID: {id_counter}")
        
        # Extract image URLs
        original_image_url = item.get('originalImage', '')
        perspective_image_url = item.get('perspectiveImage', '')
        
        # Initialize download status
        original_downloaded = ""
        annotated_downloaded = ""
        
        # Download original image
        if original_image_url:
            bucket, key, region = parse_s3_url(original_image_url)
            if bucket and key:
                download_credentials = credentials.copy()
                if region:
                    download_credentials["region"] = region
                
                file_extension = os.path.splitext(key)[1] or '.jpg'
                custom_filename = f"{id_counter}_original{file_extension}"
                
                downloaded_path = download_from_s3_with_custom_name(
                    bucket, key, download_credentials,
                    output_dir="./downloads/original/false",
                    custom_filename=custom_filename
                )
                
                if downloaded_path:
                    original_downloaded = f"downloads/original/false/{custom_filename}"
                    print(f"✓ Downloaded original image for ID {id_counter}")
                else:
                    print(f"✗ Failed to download original image for ID {id_counter}")
        
        # Download annotated image (perspectiveImage)
        if perspective_image_url:
            bucket, key, region = parse_s3_url(perspective_image_url)
            if bucket and key:
                download_credentials = credentials.copy()
                if region:
                    download_credentials["region"] = region
                
                file_extension = os.path.splitext(key)[1] or '.jpg'
                custom_filename = f"{id_counter}_annotated{file_extension}"
                
                downloaded_path = download_from_s3_with_custom_name(
                    bucket, key, download_credentials,
                    output_dir="./downloads/annotated/false",
                    custom_filename=custom_filename
                )
                
                if downloaded_path:
                    annotated_downloaded = f"downloads/annotated/false/{custom_filename}"
                    print(f"✓ Downloaded annotated image for ID {id_counter}")
                else:
                    print(f"✗ Failed to download annotated image for ID {id_counter}")
        
        # Create clean data entry
        clean_entry = {
            "id": id_counter,
            "original_image": original_image_url,
            "original_downloaded": original_downloaded,
            "annotated_image": perspective_image_url,
            "annotated_downloaded": annotated_downloaded,
            "big_rock_detected_predicted": item.get('bigParticlePresent', False),
            "big_rock_detected_annotated": ""
        }
        
        clean_data.append(clean_entry)
        id_counter += 1
    
    # Process true data (bigParticlePresent = true)
    print(f"\nProcessing {len(true_data)} items from true data (limited to 30)...")
    for idx, item in enumerate(true_data):
        print(f"\nProcessing true item {idx+1}/{len(true_data)} -> ID: {id_counter}")
        
        # Extract image URLs
        original_image_url = item.get('originalImage', '')
        perspective_image_url = item.get('perspectiveImage', '')
        
        # Initialize download status
        original_downloaded = ""
        annotated_downloaded = ""
        
        # Download original image
        if original_image_url:
            bucket, key, region = parse_s3_url(original_image_url)
            if bucket and key:
                download_credentials = credentials.copy()
                if region:
                    download_credentials["region"] = region
                
                file_extension = os.path.splitext(key)[1] or '.jpg'
                custom_filename = f"{id_counter}_original{file_extension}"
                
                downloaded_path = download_from_s3_with_custom_name(
                    bucket, key, download_credentials,
                    output_dir="./downloads/original/true",
                    custom_filename=custom_filename
                )
                
                if downloaded_path:
                    original_downloaded = f"downloads/original/true/{custom_filename}"
                    print(f"✓ Downloaded original image for ID {id_counter}")
                else:
                    print(f"✗ Failed to download original image for ID {id_counter}")
        
        # Download annotated image (perspectiveImage)
        if perspective_image_url:
            bucket, key, region = parse_s3_url(perspective_image_url)
            if bucket and key:
                download_credentials = credentials.copy()
                if region:
                    download_credentials["region"] = region
                
                file_extension = os.path.splitext(key)[1] or '.jpg'
                custom_filename = f"{id_counter}_annotated{file_extension}"
                
                downloaded_path = download_from_s3_with_custom_name(
                    bucket, key, download_credentials,
                    output_dir="./downloads/annotated/true",
                    custom_filename=custom_filename
                )
                
                if downloaded_path:
                    annotated_downloaded = f"downloads/annotated/true/{custom_filename}"
                    print(f"✓ Downloaded annotated image for ID {id_counter}")
                else:
                    print(f"✗ Failed to download annotated image for ID {id_counter}")
        
        # Create clean data entry
        clean_entry = {
            "id": id_counter,
            "original_image": original_image_url,
            "original_downloaded": original_downloaded,
            "annotated_image": perspective_image_url,
            "annotated_downloaded": annotated_downloaded,
            "big_rock_detected_predicted": item.get('bigParticlePresent', False),
            "big_rock_detected_annotated": ""
        }
        
        clean_data.append(clean_entry)
        id_counter += 1
    
    # Save clean.json
    try:
        with open('clean.json', 'w') as f:
            json.dump(clean_data, f, indent=2)
        print(f"\n✓ Successfully created clean.json with {len(clean_data)} items")
        
        # Print summary statistics
        predicted_true = sum(1 for item in clean_data if item['big_rock_detected_predicted'] is True)
        predicted_false = sum(1 for item in clean_data if item['big_rock_detected_predicted'] is False)
        successful_original_downloads = sum(1 for item in clean_data if item['original_downloaded'])
        successful_annotated_downloads = sum(1 for item in clean_data if item['annotated_downloaded'])
        
        print(f"\nSummary:")
        print(f"Total items: {len(clean_data)}")
        print(f"Successful original image downloads: {successful_original_downloads}")
        print(f"Successful annotated image downloads: {successful_annotated_downloads}")
        print(f"Predicted True (big rock present): {predicted_true}")
        print(f"Predicted False (no big rock): {predicted_false}")
        
    except Exception as e:
        print(f"Error saving clean.json: {e}")

def main():
    """
    Main function to run the processing.
    """
    print("Big Rock Data Processing Script")
    print("=" * 35)
    
    # Process JSON files and download images
    process_big_rock_data()

if __name__ == "__main__":
    main()
