pip install -e .



pip install build
python -m build

from dvr_ftp.client import get_ftp_files_filtered, download_ftp_files

# Use your credentials
creds = {"host": "192.168.15.60", "user": "dvr", "password": "1"}

# Get file paths from DVR (Depth: Date -> Channel -> Files)
files = get_ftp_files_filtered(**creds, extensions=('.mp4', '.dav'), depth_level=3)

# Download files for processing
download_ftp_files(**creds, path_list=files, target_folder="./raw_footage")