import os
import re
from urllib.parse import urlparse
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
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

def download_from_s3(bucket, object_key, credentials, output_dir="./"):
    """
    Download a file from AWS S3 using proper AWS authentication.
    
    Args:
        bucket (str): S3 bucket name
        object_key (str): S3 object key
        credentials (dict): AWS credentials
        output_dir (str): Directory to save the downloaded file
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
                print("Possible issues:")
                print("  1. Invalid AWS credentials")
                print("  2. Insufficient IAM permissions")
                print("  3. Bucket policy restrictions")
                print("  4. Object is private and requires different access method")
                return
            elif e.response['Error']['Code'] == '404':
                print("✗ Object not found")
                return
            else:
                raise e
        
        # Download the file
        s3_client.download_file(bucket, object_key, output_path)
        
        print(f"Download completed successfully: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        
    except NoCredentialsError:
        print("Error: AWS credentials not available")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket}' does not exist")
        elif error_code == 'NoSuchKey':
            print(f"Error: Object '{object_key}' does not exist in bucket '{bucket}'")
        elif error_code == 'AccessDenied' or error_code == '403':
            print(f"Error: Access denied. Check your credentials and permissions")
            print("Troubleshooting steps:")
            print("1. Verify AWS credentials are correct")
            print("2. Check IAM user has s3:GetObject permission")
            print("3. Verify bucket policy allows access")
        else:
            print(f"Error downloading from S3: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """
    Main function to run the download.
    """
    print("S3 Download Test Script")
    print("=" * 40)
    
    # Get S3 URL from user input
    s3_url = get_s3_url()
    
    # Parse the S3 URL to extract bucket, key, and region
    bucket, key, region = parse_s3_url(s3_url)
    
    if not bucket or not key:
        print("❌ Failed to parse S3 URL. Please check the format and try again.")
        return
    
    print(f"\n📋 Parsed S3 details:")
    print(f"   Bucket: {bucket}")
    print(f"   Key: {key}")
    print(f"   Region: {region}")
    
    # Get AWS credentials
    credentials = get_aws_credentials()
    
    # Update region in credentials if detected from URL
    if region:
        credentials["region"] = region
    
    # Download the file
    download_from_s3(bucket, key, credentials, output_dir="./downloads")
if __name__ == "__main__":
    main()
