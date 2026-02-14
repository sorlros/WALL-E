from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing in .env")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_supabase(file_bytes: bytes, file_name: str, bucket_name: str = "detections", content_type: str = "image/jpeg") -> str:
    """
    Uploads an image to Supabase Storage and returns the public URL.
    
    Args:
        file_bytes (bytes): The binary content of the image.
        file_name (str): The filename (e.g., 'mission_1/frame_100.jpg').
        bucket_name (str): The storage bucket (default='detections').
        content_type (str): MIME type.
        
    Returns:
        str: The public URL of the uploaded image.
    """
    if not supabase:
        raise ValueError("Supabase client is not initialized. Check .env settings.")
        
    try:
        # Upload
        # 'upsert=True' allows overwriting if file exists
        response = supabase.storage.from_(bucket_name).upload(
            file_name, 
            file_bytes, 
            {"content-type": content_type, "upsert": "true"}
        )
        
        # Get Public URL
        # Note: Bucket must be set to Public in Supabase Dashboard
        public_url_response = supabase.storage.from_(bucket_name).get_public_url(file_name)
        
        return public_url_response
        
    except Exception as e:
        print(f"Supabase Upload Error: {e}")
        return None
