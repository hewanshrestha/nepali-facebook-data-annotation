from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import os
import io
import json
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the path to service account credentials
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service-account.json')

# Root folder name for all annotation data
ROOT_FOLDER_NAME = "Nepali_Facebook_Annotation_Results"

# Your Google account email (replace with your actual email)
USER_EMAIL = "hebanshrestha12@gmail.com"  # Replace this with your email

def get_service_account_info():
    """Get service account information from either Streamlit secrets or file."""
    try:
        # First try to get from Streamlit secrets
        if 'gcp_service_account' in st.secrets:
            return st.secrets['gcp_service_account']
        
        # If not in secrets, try to read from file
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                return json.load(f)
        
        raise FileNotFoundError("No service account credentials found in Streamlit secrets or file!")
    except Exception as e:
        logger.error(f"Error getting service account info: {e}")
        raise

def get_service_account_email():
    """Get the service account email from the credentials."""
    try:
        service_account_info = get_service_account_info()
        return service_account_info.get('client_email')
    except Exception as e:
        logger.error(f"Error reading service account email: {e}")
        return None

def share_folder_with_user(service, folder_id, user_email):
    """Share a folder with a specific user."""
    try:
        user_permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': user_email
        }
        
        service.permissions().create(
            fileId=folder_id,
            body=user_permission,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"Successfully shared folder with {user_email}")
    except Exception as e:
        logger.error(f"Error sharing folder with {user_email}: {e}")
        raise

def authenticate_google_drive():
    """Authenticate with Google Drive API using service account."""
    logger.debug("Starting Google Drive authentication process...")
    
    try:
        # Get service account info from either Streamlit secrets or file
        service_account_info = get_service_account_info()
        service_account_email = service_account_info.get('client_email')
        logger.info(f"Service account email: {service_account_email}")
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # Test the connection by listing files
        results = service.files().list(
            pageSize=1,
            fields="nextPageToken, files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        logger.info("Successfully connected to Google Drive API")
        
        return service
    except Exception as e:
        logger.error(f"Error authenticating with Google Drive: {e}", exc_info=True)
        raise

def get_or_create_root_folder(service):
    """Get or create the root folder for all annotation data."""
    try:
        # Search for existing root folder
        results = service.files().list(
            q=f"name='{ROOT_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            folder_id = items[0]['id']
            logger.info(f"Found existing root folder: {ROOT_FOLDER_NAME} (ID: {folder_id})")
            return folder_id
        else:
            # Create new root folder only if it doesn't exist
            file_metadata = {
                'name': ROOT_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            folder_id = folder.get('id')
            logger.info(f"Created new root folder: {ROOT_FOLDER_NAME} (ID: {folder_id})")
            
            # Share the new folder with the user
            share_folder_with_user(service, folder_id, USER_EMAIL)
            return folder_id
            
    except Exception as e:
        logger.error(f"Error getting/creating root folder: {e}", exc_info=True)
        raise

def get_or_create_annotator_folder(service, annotator_id):
    """Get or create a folder for a specific annotator within the root folder."""
    try:
        root_folder_id = get_or_create_root_folder(service)
        
        # Search for existing annotator folder
        results = service.files().list(
            q=f"name='{annotator_id}' and '{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            # Delete existing annotator folder and its contents
            folder_id = items[0]['id']
            logger.info(f"Found existing folder for {annotator_id} (ID: {folder_id})")
            
            # List all files in the annotator folder
            all_files = []
            page_token = None
            
            while True:
                try:
                    results = service.files().list(
                        q=f"'{folder_id}' in parents and trashed=false",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType)',
                        pageToken=page_token,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                    
                    all_files.extend(results.get('files', []))
                    page_token = results.get('nextPageToken')
                    
                    if not page_token:
                        break
                        
                except Exception as e:
                    logger.error(f"Error listing files: {e}")
                    break
            
            # Delete all files in the annotator folder
            for file in all_files:
                try:
                    service.files().delete(
                        fileId=file['id'],
                        supportsAllDrives=True
                    ).execute()
                    logger.info(f"Deleted {file['mimeType']}: {file['name']} (ID: {file['id']})")
                except Exception as e:
                    logger.error(f"Error deleting {file['name']}: {e}")
            
            # Delete the annotator folder
            service.files().delete(
                fileId=folder_id,
                supportsAllDrives=True
            ).execute()
            logger.info(f"Deleted existing folder for {annotator_id}")
        
        # Create new annotator folder
        file_metadata = {
            'name': annotator_id,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [root_folder_id]
        }
        folder = service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        folder_id = folder.get('id')
        logger.info(f"Created new folder for {annotator_id} (ID: {folder_id})")
        return folder_id
        
    except Exception as e:
        logger.error(f"Error getting/creating annotator folder: {e}", exc_info=True)
        raise

def save_jsonl_to_drive(service, file_path, file_name, annotator_id):
    """Save a JSONL file to the annotator's folder in Google Drive."""
    try:
        # Get or create the annotator's folder
        folder_id = get_or_create_annotator_folder(service, annotator_id)
        logger.debug(f"Preparing to save file: {file_name} to folder: {folder_id}")
        
        # Read the new content
        with open(file_path, 'r', encoding='utf-8') as f:
            new_content = f.read().strip()
        
        # Parse new annotations
        new_annotations = []
        for line in new_content.splitlines():
            if line.strip():
                new_annotations.append(json.loads(line))
        
        # Check if the file already exists in the specified folder
        results = service.files().list(
            q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        
        if items:
            # File exists, update it
            file_id = items[0]['id']
            logger.debug(f"File already exists (ID: {file_id}), updating content")
            
            # Read existing content
            existing_content = read_jsonl_from_drive(service, file_id)
            existing_annotations = []
            for line in existing_content.splitlines():
                if line.strip():
                    existing_annotations.append(json.loads(line))
            
            # Create a set of existing item IDs
            existing_item_ids = {ann['item_id'] for ann in existing_annotations}
            
            # Filter out duplicates from new annotations
            unique_new_annotations = [
                ann for ann in new_annotations 
                if ann['item_id'] not in existing_item_ids
            ]
            
            # Combine existing and new unique annotations
            combined_annotations = existing_annotations + unique_new_annotations
            
            # Convert back to JSONL format
            combined_content = '\n'.join(
                json.dumps(ann, ensure_ascii=False) for ann in combined_annotations
            )
            
            # Create a temporary file with the combined content
            temp_file = 'temp_combined.jsonl'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            # Update the file in Drive
            media = MediaFileUpload(temp_file, mimetype='application/json', resumable=True)
            service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()
            
            # Clean up temporary file
            os.remove(temp_file)
            logger.info(f"Successfully updated file with {len(unique_new_annotations)} new annotations")
        else:
            # File doesn't exist, create it
            file_metadata = {
                'name': file_name,
                'parents': [folder_id],
                'mimeType': 'application/json'
            }
            
            logger.debug(f"Creating new file: {file_name} in folder: {folder_id}")
            media = MediaFileUpload(file_path, mimetype='application/json', resumable=True)
            file_result = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"Successfully created file: {file_name} (ID: {file_result.get('id')})")
        
        logger.debug(f"Successfully saved file: {file_name} to folder: {folder_id}")
    except Exception as e:
        logger.error(f"Error saving file to Google Drive: {str(e)}", exc_info=True)
        raise

def read_jsonl_from_drive(service, file_id):
    """Read a JSONL file from Google Drive."""
    try:
        logger.debug(f"Reading file with ID: {file_id}")
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
        fh.seek(0)
        content = fh.read().decode('utf-8')
        logger.debug("Successfully read file from Google Drive")
        return content
    except Exception as e:
        logger.error(f"Error reading file from Google Drive: {str(e)}", exc_info=True)
        raise

def update_jsonl_in_drive(service, file_id, content):
    """Replace the entire content of an existing JSONL file in Google Drive."""
    try:
        logger.debug(f"Updating file content in Drive (file ID: {file_id})")
        
        # Create a temporary file with the new content
        temp_file = f'temp_update_{file_id}.jsonl'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update the file in Drive
        media = MediaFileUpload(temp_file, mimetype='application/json', resumable=True)
        service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()
        
        # Clean up temporary file
        os.remove(temp_file)
        logger.debug("Successfully updated file content in Google Drive")
    except Exception as e:
        logger.error(f"Error updating file in Google Drive: {str(e)}", exc_info=True)
        raise

def append_to_jsonl_in_drive(service, file_id, new_content):
    """Append new content to an existing JSONL file in Google Drive."""
    try:
        logger.debug(f"Appending content to file in Drive (file ID: {file_id})")
        
        # Read existing content
        existing_content = read_jsonl_from_drive(service, file_id)
        logger.debug("Successfully read existing content from Drive")
        
        # Combine existing content with new content
        existing_content = existing_content.strip()
        if existing_content:
            combined_content = existing_content + '\n' + new_content
        else:
            combined_content = new_content
            
        logger.debug("Combined existing and new content")
        
        # Update the file with combined content
        update_jsonl_in_drive(service, file_id, combined_content)
        logger.debug("Successfully appended content to file in Google Drive")
    except Exception as e:
        logger.error(f"Error appending to file in Google Drive: {str(e)}", exc_info=True)
        raise

def list_files_in_folder(service, folder_id):
    """List all files in a specific Google Drive folder."""
    try:
        logger.debug(f"Listing files in folder: {folder_id}")
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, createdTime, modifiedTime)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        logger.debug(f"Found {len(items)} files in folder")
        return items
    except Exception as e:
        logger.error(f"Error listing files in folder: {str(e)}", exc_info=True)
        raise

def delete_file_from_drive(service, file_id):
    """Delete a file from Google Drive."""
    try:
        logger.debug(f"Deleting file with ID: {file_id}")
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        logger.info(f"Successfully deleted file with ID: {file_id}")
    except Exception as e:
        logger.error(f"Error deleting file from Google Drive: {str(e)}", exc_info=True)
        raise

def delete_root_folder(service):
    """Delete the root folder and all its contents."""
    try:
        # Search for the root folder
        results = service.files().list(
            q=f"name='{ROOT_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            logger.warning(f"Root folder '{ROOT_FOLDER_NAME}' not found")
            return False
        
        root_folder_id = items[0]['id']
        logger.info(f"Found root folder: {ROOT_FOLDER_NAME} (ID: {root_folder_id})")
        
        # List all files in the root folder and its subfolders
        all_files = []
        page_token = None
        
        while True:
            try:
                # List all files in the root folder
                results = service.files().list(
                    q=f"'{root_folder_id}' in parents and trashed=false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType)',
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                all_files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                break
        
        # Delete all files and subfolders
        for file in all_files:
            try:
                service.files().delete(
                    fileId=file['id'],
                    supportsAllDrives=True
                ).execute()
                logger.info(f"Deleted {file['mimeType']}: {file['name']} (ID: {file['id']})")
            except Exception as e:
                logger.error(f"Error deleting {file['name']}: {e}")
        
        # Finally, delete the root folder
        try:
            service.files().delete(
                fileId=root_folder_id,
                supportsAllDrives=True
            ).execute()
            logger.info(f"Successfully deleted root folder: {ROOT_FOLDER_NAME}")
            return True
        except Exception as e:
            logger.error(f"Error deleting root folder: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in delete_root_folder: {e}", exc_info=True)
        return False