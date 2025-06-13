# Nepali Facebook Data Annotation

This application provides an interface for annotating Nepali Facebook posts with claims and checkworthiness assessments.

## Setup

### Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure Supabase (optional for local development):
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Edit the file and add your Supabase project URL and API key
   - Set `USE_SUPABASE = "true"` if you want to use Supabase storage

4. Run the application:
   ```
   streamlit run annotation_interface/app.py
   ```

### Deployment on Streamlit Cloud

1. Push your code to a GitHub repository
2. Set up a new app on Streamlit Cloud
3. Configure secrets in Streamlit Cloud dashboard:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase API key
   - `USE_SUPABASE`: Set to "true"
   
4. Deploy the app

## Supabase Setup

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project
3. Set up storage buckets:
   - Go to Storage in dashboard
   - Create a bucket named `annotation-files` for storing JSONL files
   - Create a bucket named `images` for storing images
   - Configure bucket permissions (public or RLS)
4. Get your project URL and API key from the project settings

## Data Storage

The application can operate in two modes:

1. **Local Storage**: All annotations are stored in local JSONL files
2. **Supabase Storage**: Annotations are stored both locally and in Supabase cloud storage

The storage mode is controlled by the `USE_SUPABASE` environment variable or secret.