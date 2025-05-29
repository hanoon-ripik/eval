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

def get_s3_url():
    """
    Get S3 URL from user input.
    
    Returns:
        str: S3 URL
    """
    s3_url = input("Enter S3 URL: ").strip()
    return s3_url

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

def process_raw_json_and_download():
    """
    Process raw.json file and create clean.json with downloaded images for Coil ID data.
    """
    print("Processing Coil ID raw.json and downloading images...")
    
    # Read raw.json
    try:
        with open('raw.json', 'r') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print("Error: raw.json not found in current directory")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing raw.json: {e}")
        return
    
    print(f"Found {len(raw_data)} items in raw.json")
    
    # Process all items (up to 200)
    items_to_process = raw_data[:200]
    print(f"Processing {len(items_to_process)} items")
    
    # Get AWS credentials
    credentials = get_aws_credentials()
    
    # Create clean data structure
    clean_data = []
    
    # Create downloads directory if it doesn't exist
    os.makedirs("./downloads", exist_ok=True)
    
    # Process each item, using 1-based IDs as requested in the example
    for idx, item in enumerate(items_to_process):
        i = idx + 1  # Start IDs from 1 as shown in the example
        print(f"\nProcessing item {idx+1}/{len(items_to_process)} -> ID: {i}")
        
        # Extract original_image URL directly from originalImage field
        original_image_url = ""
        if 'originalImage' in item:
            # For coil_id, originalImage is a direct string, not an object with camera keys
            if isinstance(item['originalImage'], str):
                original_image_url = item['originalImage']
        
        if not original_image_url:
            print(f"Warning: No bay front camera image found for item {i}")
            # Create entry with empty download_image
            clean_entry = {
                "id": i,
                "original_image": "",
                "download_image": "",
                "ocr_predicted": "",
                "ocr_annotated": ""
            }
            clean_data.append(clean_entry)
            continue
        
        # Parse S3 URL
        bucket, key, region = parse_s3_url(original_image_url)
        if not bucket or not key:
            print(f"Warning: Could not parse S3 URL for item {i}: {original_image_url}")
            # Create entry with empty download_image
            clean_entry = {
                "id": i,
                "original_image": original_image_url,
                "download_image": "",
                "ocr_predicted": "",
                "ocr_annotated": ""
            }
            clean_data.append(clean_entry)
            continue
        
        # Update region in credentials if detected from URL
        download_credentials = credentials.copy()
        if region:
            download_credentials["region"] = region
        
        # Create custom filename with ID
        file_extension = os.path.splitext(key)[1] or '.jpg'
        custom_filename = f"{i}{file_extension}"
        
        # Download the image
        downloaded_path = download_from_s3_with_custom_name(
            bucket, key, download_credentials, 
            output_dir="./downloads", 
            custom_filename=custom_filename
        )
        
        # Extract OCR predicted value from coilId
        ocr_predicted = ""
        if 'coilId' in item:
            ocr_predicted = str(item['coilId']).strip()
        
        # Create clean data entry
        clean_entry = {
            "id": i,
            "original_image": original_image_url,
            "download_image": custom_filename if downloaded_path else "",
            "ocr_predicted": ocr_predicted,
            "ocr_annotated": ""
        }
        
        clean_data.append(clean_entry)
        
        if downloaded_path:
            print(f"✓ Successfully processed item {i}")
        else:
            print(f"✗ Failed to download image for item {i}")
    
    # Save clean.json
    try:
        with open('clean.json', 'w') as f:
            json.dump(clean_data, f, indent=2)
        print(f"\n✓ Successfully created clean.json with {len(clean_data)} items (all available items processed)")
    except Exception as e:
        print(f"Error saving clean.json: {e}")

def main():
    """
    Main function to run the processing.
    """
    print("Coil ID Data Processing Script")
    print("=" * 40)
    
    # Process raw.json and download images
    process_raw_json_and_download()

if __name__ == "__main__":
    main()
