# Nepali Facebook Image-Text Annotation Interface

This is a Streamlit-based annotation interface for labeling Nepali Facebook image-text pairs for claim detection and checkworthiness analysis.

## Features

- Multi-step annotation process (Claim Detection → Checkworthiness)
- Image-text pair display
- Per-annotator progress tracking
- Guidelines panel
- Session management
- Data logging and export functionality

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure your data is properly organized:
   - Place your image-text pairs in the `dataset(original)` directory
   - Each item should have an image file and corresponding text
   - The data should be in JSON format with the following structure:
     ```json
     {
       "id": "unique_id",
       "image_path": "path/to/image.jpg",
       "text": "Nepali text content"
     }
     ```

## Running the Interface

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Enter your annotator ID to begin

## Usage

1. **Login**: Enter your unique annotator ID in the sidebar
2. **Review Guidelines**: Read the annotation guidelines in the sidebar
3. **Annotation Process**:
   - View the image-text pair
   - First, determine if it's a claim
   - If it's a claim, determine if it's checkworthy
   - Submit your annotation
4. **Track Progress**: View your annotation count in the sidebar

## Data Storage

- Annotations are saved in the `annotations` directory
- Each annotation is stored as a JSON file with timestamp
- Logs are maintained in `annotation_logs.log`

## Admin Features

To view annotation progress and analyze results:
1. Check the `annotations` directory for individual annotation files
2. Review the log file for detailed activity tracking
3. Use the JSON files to analyze inter-annotator agreement and quality

## Support

For any issues or questions, please contact the project administrator. 