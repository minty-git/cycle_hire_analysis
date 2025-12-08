import os
import boto3
from botocore.exceptions import NoCredentialsError
# Import the necessary components for unsigned requests
from botocore import UNSIGNED
from botocore.config import Config

# --- Configuration ---
# Set the number of files to download from each source. Use 'None' to download all.
FILE_LIMIT = 50000
FILE_EXTENSIONS = ('.csv', '.zip')

BUCKETS_TO_DOWNLOAD = {
    # Bucket name is the domain itself for the TfL data
    "TfL_Cycling": {
        "name": "cycling.data.tfl.gov.uk",
        "directory": "tfl_cycling_data"
    },
    # The 'tripdata' URL points directly to an S3 bucket
    "NYC_CitiBike": {
        "name": "tripdata", 
        "directory": "citibike_trip_data"
    }
}

# --- Core Functions (Updated) ---

def create_directory(path):
    """Creates a directory if it does not already exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_s3_files(bucket_name, target_dir):
    """
    Connects to the public S3 bucket and downloads files matching the criteria
    using an unsigned request configuration.
    """
    print(f"\n--- Connecting to Public S3 Bucket: {bucket_name} ---")
    create_directory(target_dir)
    
    # 🌟 KEY CHANGE: Create the S3 client using an UNSIGNED configuration.
    # This prevents the "NoCredentialsError" for public buckets.
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    file_count = 0
    
    try:
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' not in response:
            print(f"Bucket '{bucket_name}' is empty or files are not accessible.")
            return

        # Filter, sort, and download the files
        files = [
            obj for obj in response['Contents'] 
            if obj['Key'].lower().endswith(FILE_EXTENSIONS) and obj['Size'] > 0
            and not obj['Key'].lower().startswith("JC-")
        ]
        
        # Sort by the LastModified timestamp in descending order (most recent first)
        files.sort(key=lambda x: x['LastModified'], reverse=True)

        for obj in files:
            key = obj['Key']
            # Only download files that are not root folders or partial directories
            if key.endswith('/'): 
                continue

            local_path = os.path.join(target_dir, os.path.basename(key))

            if os.path.exists(local_path):
            
                print(f"  Skipping: {key}...")
                continue
            
            print(f"  Downloading: {key}...")
            
            # Download the file
            s3.download_file(bucket_name, key, local_path)
            
            print(f"  Successfully saved to: {local_path}")
            
            file_count += 1
            
            # Check the download limit
            if FILE_LIMIT is not None and file_count >= FILE_LIMIT:
                print(f"\n[Limit reached] Stopped after downloading the first {FILE_LIMIT} files.")
                break

        if file_count == 0:
            print(f"No matching files found in bucket '{bucket_name}'.")
            
    except Exception as e:
        print(f"An error occurred while accessing the bucket: {e}")

def main():
    """Main function to run the downloading process for all configured buckets."""
    
    print("Starting S3 Data Downloader...")
    
    for name, config in BUCKETS_TO_DOWNLOAD.items():
        download_s3_files(config['name'], config['directory'])

    print("\n\n✅ All data processing complete.")

if __name__ == "__main__":
    main()