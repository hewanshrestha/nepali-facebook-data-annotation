# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from PIL import Image
import logging
from pathlib import Path
import time
from google_drive_utils import (
    authenticate_google_drive,
    save_jsonl_to_drive,
    read_jsonl_from_drive,
    get_or_create_annotator_folder,
    get_or_create_root_folder
)
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set default level to INFO
logger = logging.getLogger(__name__)

# Disable watchdog debug messages
logging.getLogger('watchdog').setLevel(logging.WARNING)

# Set page config first
st.set_page_config(
    page_title="Nepali Facebook Claim Annotation",
    page_icon="📝",
    layout="wide"
)

# Constants
IMAGES_DIR = "pilot_data/images"
DATASET_FILE = "pilot_data/filtered_posts.json"
BASE_DIR = "annotation_interface"
GUIDELINES_FILE = "annotation_interface/guidelines.md"
USE_GOOGLE_DRIVE = True  # Set to False to use local storage only

# Valid annotator IDs
VALID_ANNOTATORS = [f"annotator_{i:02d}" for i in range(1, 5)]  # Creates annotator_01 through annotator_04

def get_annotator_dirs(annotator_id):
    """Get the annotation and log directories for an annotator"""
    if annotator_id not in VALID_ANNOTATORS:
        raise ValueError(f"Invalid annotator ID. Must be one of: {', '.join(VALID_ANNOTATORS)}")
    
    annotator_dir = os.path.join(BASE_DIR, annotator_id)
    annotations_dir = os.path.join(annotator_dir, "annotations")
    logs_dir = os.path.join(annotator_dir, "logs")
    
    # Create directories if they don't exist
    os.makedirs(annotations_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    return annotations_dir, logs_dir

# Configure logging
def setup_logging(annotator_id):
    """Set up logging for a specific annotator"""
    global logger
    _, logs_dir = get_annotator_dirs(annotator_id)
    log_file = os.path.join(logs_dir, 'annotation_logs.log')
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Annotation session started for {annotator_id}")
    return logger

# Custom CSS (without .stRadio to avoid interference)
st.markdown("""
<style>
    .claim-text-box {
        background-color: #fffbe6;
        border: 3px solid #d4af37;
        border-radius: 12px;
        padding: 25px;
        margin: 0 0 30px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        max-width: 800px;
        width: fit-content;
        min-width: 300px;
    }
    .claim-text {
        font-size: 20px;
        line-height: 1.6;
        font-weight: 500;
        color: #333;
        font-family: 'Noto Sans Devanagari', Arial, sans-serif;
        text-align: justify;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .step-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 10px 15px;
        margin: 0 0 15px 0;
        border-radius: 4px;
        max-width: 800px;
        width: fit-content;
    }
    .step-box-2 {
        background-color: #fff3e0;
        border-left: 4px solid #f57c00;
        padding: 10px 15px;
        margin: 0 0 15px 0;
        border-radius: 4px;
        max-width: 800px;
        width: fit-content;
    }
    .step-text {
        font-size: 14px;
        font-weight: 500;
        color: #0d47a1;
        margin: 0;
        line-height: 1.4;
    }
    .step-text-2 {
        font-size: 14px;
        font-weight: 500;
        color: #e65100;
        margin: 0;
        line-height: 1.4;
    }
    .choice-container {
        display: flex;
        gap: 40px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def load_guidelines():
    """Load annotation guidelines from markdown file"""
    try:
        with open(GUIDELINES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Replace <br> with actual line breaks
            content = content.replace('<br>', '\n')
            return content
    except FileNotFoundError:
        return "Guidelines file not found."

def load_dataset():
    """Load the dataset of image-text pairs"""
    try:
        with open(DATASET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to DataFrame and add unique IDs
        df = pd.DataFrame(data)
        df['id'] = [f"item_{i}" for i in range(len(df))]
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return pd.DataFrame()

def save_annotation(annotator_id, item_id, annotation, current_item):
    """Save annotation to a JSONL file (local and/or Google Drive)"""
    logger.debug(f"Starting save_annotation for item {item_id}")
    annotations_dir, _ = get_annotator_dirs(annotator_id)
    jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    annotation_data = {
        "annotator_id": annotator_id,
        "item_id": item_id,
        "timestamp": timestamp,
        "text": current_item["text"],
        "image_id": current_item["image_id"],
        "annotation": annotation
    }
    
    # Convert to JSON string
    json_line = json.dumps(annotation_data, ensure_ascii=False)
    
    if USE_GOOGLE_DRIVE:
        logger.debug("Google Drive storage is enabled, saving to Drive only")
        try:
            # Create a temporary file for Google Drive upload
            temp_file = 'temp_annotation.jsonl'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(json_line + '\n')
            
            logger.debug("Attempting to authenticate with Google Drive")
            service = authenticate_google_drive()
            logger.debug("Successfully authenticated with Google Drive")
            
            # Save the file to Google Drive with the correct name
            file_name = f"{annotator_id}_annotations.jsonl"
            logger.debug(f"Saving file to Google Drive with name: {file_name}")
            save_jsonl_to_drive(service, temp_file, file_name, annotator_id)
            logger.info(f"Annotation saved to Google Drive for item {item_id}")
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            logger.error(f"Error saving to Google Drive: {e}", exc_info=True)
            raise
    else:
        # Save locally only if Google Drive is not enabled
        logger.debug("Google Drive storage is disabled, saving locally")
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json_line + '\n')
        logger.debug(f"Saved annotation locally to {jsonl_file}")
    
    logger.info(f"Annotation saved for item {item_id}")

def get_annotation_progress(annotator_id):
    """Get annotation progress for an annotator from JSONL file (local or Google Drive)"""
    annotations_dir, _ = get_annotator_dirs(annotator_id)
    annotations = []
    
    if USE_GOOGLE_DRIVE:
        try:
            service = authenticate_google_drive()
            # Get the annotator's folder
            folder_id = get_or_create_annotator_folder(service, annotator_id)
            # Search for the file
            results = service.files().list(
                q=f"name='{annotator_id}_annotations.jsonl' and '{folder_id}' in parents",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            items = results.get('files', [])
            
            if items:
                file_id = items[0]['id']
                content = read_jsonl_from_drive(service, file_id)
                for line in content.splitlines():
                    if line.strip():
                        annotations.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error reading from Google Drive: {e}", exc_info=True)
            raise
    else:
        # Use local file
        jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
        if os.path.exists(jsonl_file):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        annotations.append(json.loads(line))
    
    return annotations

def get_annotator_items(df, annotator_id):
    """Get the items assigned to a specific annotator"""
    # Get the annotator number (e.g., "01" from "annotator_01")
    annotator_num = int(annotator_id.split('_')[1])
    total_annotators = len(VALID_ANNOTATORS)
    
    # Calculate the items per annotator
    total_items = len(df)
    items_per_annotator = total_items // total_annotators
    
    # Calculate the start and end indices for this annotator
    start_idx = (annotator_num - 1) * items_per_annotator
    end_idx = start_idx + items_per_annotator if annotator_num < total_annotators else total_items
    
    # Get the assigned items
    assigned_items = df.iloc[start_idx:end_idx].copy()
    return assigned_items

def get_next_unannotated_item(annotator_id, df):
    """Get the next unannotated item for the annotator from their assigned items"""
    # Get only the items assigned to this annotator
    assigned_items = get_annotator_items(df, annotator_id)
    
    annotations_dir, _ = get_annotator_dirs(annotator_id)
    jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
    annotated_items = set()
    
    if os.path.exists(jsonl_file):
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    data = json.loads(line)
                    annotated_items.add(data['item_id'])
    
    for idx, row in assigned_items.iterrows():
        if row['id'] not in annotated_items:
            return row
    return None

def get_previous_annotations(annotator_id):
    """Get all previous annotations for an annotator"""
    if USE_GOOGLE_DRIVE:
        return get_annotation_progress(annotator_id)
    else:
        annotations_dir, _ = get_annotator_dirs(annotator_id)
        jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
        annotations = []
        
        if os.path.exists(jsonl_file):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        annotations.append(json.loads(line))
        
        return annotations

def update_annotation(annotator_id, item_id, new_annotation, current_item):
    """Update an existing annotation"""
    annotations_dir, _ = get_annotator_dirs(annotator_id)
    jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Read all annotations
    annotations = get_previous_annotations(annotator_id)
    
    # Find and update the specific annotation
    updated = False
    for i, ann in enumerate(annotations):
        if ann['item_id'] == item_id:
            annotations[i] = {
                "annotator_id": annotator_id,
                "item_id": item_id,
                "timestamp": timestamp,
                "text": current_item["text"],
                "image_id": current_item["image_id"],
                "annotation": new_annotation
            }
            updated = True
            break
    
    # Convert annotations back to JSONL format
    updated_content = ""
    for ann in annotations:
        updated_content += json.dumps(ann, ensure_ascii=False) + '\n'
    
    # Update local file
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    # If Google Drive is enabled, update there as well
    if USE_GOOGLE_DRIVE:
        try:
            service = authenticate_google_drive()
            # Get the annotator's folder
            folder_id = get_or_create_annotator_folder(service, annotator_id)
            results = service.files().list(
                q=f"name='{annotator_id}_annotations.jsonl' and '{folder_id}' in parents",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            items = results.get('files', [])
            
            if items:
                file_id = items[0]['id']
                # Create a temporary file with the updated content
                temp_file = 'temp_update.jsonl'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                # Update the file in Drive
                media = MediaFileUpload(temp_file, mimetype='application/json', resumable=True)
                service.files().update(
                    fileId=file_id,
                    media_body=media,
                    supportsAllDrives=True
                ).execute()
                
                # Clean up temporary file
                os.remove(temp_file)
                logger.info(f"Annotation updated in Google Drive for item {item_id}")
        except Exception as e:
            logger.error(f"Error updating in Google Drive: {e}")
    
    logger.info(f"Annotation updated for item {item_id}")
    return updated

def save_all_temporary_annotations(annotator_id):
    """Save all temporary annotations to Google Drive"""
    try:
        if not st.session_state.temp_annotations:
            st.warning("No temporary annotations to save!")
            return False
        
        logger.info(f"Saving {len(st.session_state.temp_annotations)} temporary annotations to Google Drive")
        
        # Convert temporary annotations to JSONL format
        jsonl_content = ""
        for item_id, annotation_data in st.session_state.temp_annotations.items():
            jsonl_content += json.dumps(annotation_data, ensure_ascii=False) + '\n'
        
        if USE_GOOGLE_DRIVE:
            # Create a temporary file
            temp_file = f'temp_batch_annotations_{annotator_id}.jsonl'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(jsonl_content)
            
            try:
                # Authenticate and get service
                service = authenticate_google_drive()
                logger.debug("Successfully authenticated with Google Drive for batch save")
                
                # Save the file to Google Drive
                file_name = f"{annotator_id}_annotations.jsonl"
                logger.debug(f"Saving batch annotations to Google Drive with name: {file_name}")
                save_jsonl_to_drive(service, temp_file, file_name, annotator_id)
                logger.info("Successfully saved batch annotations to Google Drive")
                
                return True
                    
            except Exception as e:
                logger.error(f"Error in batch save to Google Drive: {str(e)}", exc_info=True)
                raise
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug("Cleaned up temporary file")
        else:
            # Save locally
            annotations_dir, _ = get_annotator_dirs(annotator_id)
            jsonl_file = os.path.join(annotations_dir, f"{annotator_id}_annotations.jsonl")
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                f.write(jsonl_content)
            logger.info(f"Successfully saved {len(st.session_state.temp_annotations)} annotations locally")
            return True
            
    except Exception as e:
        logger.error(f"Error in save_all_temporary_annotations: {str(e)}", exc_info=True)
        return False

def main():
    # Initialize session state with separate tracking variables
    if 'current_item' not in st.session_state:
        st.session_state.current_item = None
    if 'is_previous' not in st.session_state:
        st.session_state.is_previous = False
    if 'prev_annotation_index' not in st.session_state:
        st.session_state.prev_annotation_index = -1
    if 'is_update' not in st.session_state:
        st.session_state.is_update = False
    if 'temp_annotations' not in st.session_state:
        st.session_state.temp_annotations = {}
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'submitted_annotations' not in st.session_state:
        st.session_state.submitted_annotations = 0
    
    # Use separate tracking variables (NOT widget keys)
    if 'display_claim_status' not in st.session_state:
        st.session_state.display_claim_status = "No Claim"
    if 'display_checkworthiness' not in st.session_state:
        st.session_state.display_checkworthiness = "Checkworthy"

    # Sidebar for annotator login and guidelines
    with st.sidebar:
        st.title("Annotation Interface")
        
        # Annotator login
        annotator_id = st.text_input("Enter your annotator ID:")
        if not annotator_id:
            st.warning("Please enter your annotator ID to begin.")
            return
        
        # Validate annotator ID
        if annotator_id not in VALID_ANNOTATORS:
            st.error(f"Invalid annotator ID. Please use one of: {', '.join(VALID_ANNOTATORS)}")
            return
        
        # Set up logging for the selected annotator
        logger = setup_logging(annotator_id)
        
        # Guidelines
        st.header("Guidelines")
        guidelines = load_guidelines()
        st.markdown(guidelines)
        
        # Progress tracking
        st.header("Your Progress")
        assigned_items = get_annotator_items(load_dataset(), annotator_id)
        temp_annotations_count = len(st.session_state.temp_annotations)
        total_annotations = temp_annotations_count + st.session_state.submitted_annotations
        st.write(f"Total annotations: {total_annotations}")
        st.write(f"Total items assigned: {len(assigned_items)}")
        st.write(f"Remaining items: {len(assigned_items) - total_annotations}")
        
        # Add intermediate save button
        if temp_annotations_count > 0:
            # st.write(f"Temporary annotations: {temp_annotations_count}")
            if st.button("💾 Save Progress", help="Save your current annotations to Google Drive"):
                with st.spinner("Saving annotations..."):
                    success = save_all_temporary_annotations(annotator_id)
                    if success:
                        st.success(f"Successfully saved {temp_annotations_count} annotations!")
                        # Update counters
                        st.session_state.submitted_annotations += temp_annotations_count
                        st.session_state.temp_annotations = {}
                        st.rerun()
                    else:
                        st.error("Failed to save annotations. Please try again.")
    
    # Main content area
    st.title("Nepali Facebook Claim Annotation")
    
    # Load dataset
    df = load_dataset()
    if df.empty:
        st.error("No data available for annotation.")
        return

    # Get assigned items for this annotator
    assigned_items = get_annotator_items(df, annotator_id)
    
    # Get current item
    if st.session_state.current_index >= len(assigned_items):
        st.success("Congratulations! You have completed all annotations.")
        
        # Add Submit All button below congratulations message
        if len(st.session_state.temp_annotations) > 0:
            st.info(f"You have {len(st.session_state.temp_annotations)} unsaved annotations.")
            if st.button("Submit All Annotations", type="primary"):
                with st.spinner("Submitting all annotations..."):
                    success = save_all_temporary_annotations(annotator_id)
                    if success:
                        st.success(f"Successfully submitted {len(st.session_state.temp_annotations)} annotations!")
                        # Update submitted annotations count and clear temporary storage
                        st.session_state.submitted_annotations += len(st.session_state.temp_annotations)
                        st.session_state.temp_annotations = {}
                        st.rerun()
                    else:
                        st.error("Failed to submit annotations. Please try again.")
        else:
            st.info("All annotations have been submitted!")
        return
    
    # Display important note in red (only when not on congratulations page)
    st.markdown("""
        <div style="color: #ff0000; font-weight: bold; font-size: 16px; margin: 15px 0; padding: 10px; border-left: 4px solid #ff0000; background-color: #fff0f0;">
            Note: Consider both the image and text together when making your decision
        </div>
    """, unsafe_allow_html=True)
    
    current_item = assigned_items.iloc[st.session_state.current_index]
    st.session_state.current_item = current_item
    
    # Check if this item has a temporary annotation
    if current_item['id'] in st.session_state.temp_annotations:
        temp_ann = st.session_state.temp_annotations[current_item['id']]
        st.session_state.display_claim_status = temp_ann['annotation']['claim_status']
        if temp_ann['annotation']['claim_status'] == "Claim":
            st.session_state.display_checkworthiness = temp_ann['annotation']['checkworthiness']
    else:
        st.session_state.display_claim_status = "No Claim"
        st.session_state.display_checkworthiness = "Checkworthy"

    # Display text
    st.markdown('<h3 style="margin: 0 0 10px 0;">Claim Text</h3>', unsafe_allow_html=True)
    st.markdown(f'''
        <div class="claim-text-box">
            <div class="claim-text">{current_item["text"]}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # Display image
    st.markdown('<h3 style="margin: 0 0 10px 0;">Associated Image</h3>', unsafe_allow_html=True)
    try:
        image_path = os.path.join(IMAGES_DIR, current_item['image_id'])
        image = Image.open(image_path)
        st.image(image, width=600)
        st.write("")
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
    
    # Annotation form
    st.markdown('<h3 style="margin: 0 0 10px 0;">Label the Claim</h3>', unsafe_allow_html=True)
    
    # Step 1: Claim Detection
    st.markdown('''
        <div class="step-box">
            <p class="step-text"><b>Task 1: Claim Detection</b> <br><br> Please read the text above and examine the image. Does this content make a factual claim that can be verified?</p>
        </div>
    ''', unsafe_allow_html=True)
    
    claim_options = ["Claim", "No Claim"]
    claim_index = 0 if st.session_state.display_claim_status == "Claim" else 1
    claim_status = st.radio(
        "Is this a claim?",
        claim_options,
        index=claim_index,
        horizontal=True,
        label_visibility="collapsed"
    )

    # Task 2: Checkworthiness Detection
    checkworthiness = None
    if claim_status == "Claim":
        st.markdown('''
            <div class="step-box-2">
                <p class="step-text-2"><b>Task 2: Checkworthiness Detection</b> <br><br> Since you selected 'Claim', please determine if this claim is worth fact-checking. Consider the potential impact and verifiability of the statement.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        checkworthy_options = ["Checkworthy", "Not Checkworthy"]
        checkworthy_index = 0 if st.session_state.display_checkworthiness == "Checkworthy" else 1
        checkworthiness = st.radio(
            "Is this claim checkworthy?",
            checkworthy_options,
            index=checkworthy_index,
            horizontal=True,
            label_visibility="collapsed"
        )

    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Previous", disabled=st.session_state.current_index == 0):
            st.session_state.current_index -= 1
            st.rerun()
    
    with col2:
        if st.button("Next"):
            # Save current annotation to temporary storage
            annotation = {
                "claim_status": claim_status,
                "checkworthiness": checkworthiness if claim_status == "Claim" else None
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.temp_annotations[current_item['id']] = {
                "annotator_id": annotator_id,
                "item_id": current_item['id'],
                "timestamp": timestamp,
                "text": current_item["text"],
                "image_id": current_item["image_id"],
                "annotation": annotation
            }
            
            st.session_state.current_index += 1
            st.rerun()

if __name__ == "__main__":
    main()