from ftplib import FTP
import os

def get_ftp_files_filtered(host, user, password, initial_dir="/", extensions=None, depth_level=1):
    """
    Search for file paths on FTP with extension filtering and recursion depth control.
    """
    found_files = []
    
    # If no filters provided, accept any file
    if extensions is None:
        extensions = ("",) 

    def navigate(ftp, current_dir, current_level):
        # Depth control: stops if current level exceeds the limit
        if current_level > depth_level:
            return

        try:
            ftp.cwd(current_dir)
            items = []
            ftp.retrlines('LIST', items.append)
            
            for item in items:
                columns = item.split()
                if len(columns) < 9: continue
                
                name = " ".join(columns[8:])
                # Clean path to avoid double slashes
                full_path = f"{current_dir}/{name}".replace("//", "/")
                
                if item.startswith('d'):  # If it is a directory
                    if name not in [".", ".."]:
                        # Recursive call incrementing level
                        navigate(ftp, full_path, current_level + 1)
                        ftp.cwd("..") 
                else:
                    # Check if the file ends with allowed extensions
                    if name.lower().endswith(extensions):
                        found_files.append(full_path)
                        
        except Exception as e:
            print(f"Error accessing {current_dir}: {e}")

    # Main connection flow
    try:
        with FTP(host) as ftp:
            ftp.login(user=user, passwd=password)
            print(f"Connected to {host}. Searching files up to level {depth_level}...")
            navigate(ftp, initial_dir, 1)
    except Exception as e:
        print(f"FTP Connection Error: {e}")

    return found_files

def download_ftp_files(host, user, password, path_list, target_folder="downloads"):
    """
    Downloads files from a list of FTP paths to a local folder.
    """
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"Folder '{target_folder}' created.")

    try:
        with FTP(host) as ftp:
            ftp.login(user=user, passwd=password)
            
            for remote_path in path_list:
                file_name = os.path.basename(remote_path)
                local_path = os.path.join(target_folder, file_name)
                
                print(f"Downloading: {file_name}...", end=" ", flush=True)
                
                try:
                    with open(local_path, 'wb') as local_file:
                        # RETR command for binary download
                        ftp.retrbinary(f"RETR {remote_path}", local_file.write)
                    print("Done!")
                except Exception as e:
                    print(f"Failed to download {file_name}: {e}")
                    
    except Exception as e:
        print(f"Connection Error: {e}")