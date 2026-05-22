"""
Script to delete all files from Supabase Storage buckets.
Run this after truncating the database to clean up storage.
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment variables")

supabase = create_client(url, key)

# List of storage buckets to clear
BUCKETS_TO_CLEAR = [
    "intake-uploads",  # Client intake documents and IDs
    "documents",       # Case documents
    "profile-photos",  # Client profile photos
    "avatars",         # User avatars
]

def clear_bucket(bucket_name: str):
    """Delete all files from a specific bucket."""
    try:
        print(f"Clearing bucket: {bucket_name}")
        
        # List all files in the bucket
        files = supabase.storage.from_(bucket_name).list()
        
        if not files:
            print(f"  Bucket '{bucket_name}' is already empty")
            return
        
        # Delete each file
        file_count = len(files)
        for file in files:
            try:
                supabase.storage.from_(bucket_name).remove([file['name']])
                print(f"  Deleted: {file['name']}")
            except Exception as e:
                print(f"  Error deleting {file['name']}: {e}")
        
        print(f"  Cleared {file_count} files from '{bucket_name}'")
        
    except Exception as e:
        print(f"Error clearing bucket '{bucket_name}': {e}")
        print(f"  Bucket might not exist or you might not have permissions")

def main():
    print("=" * 60)
    print("SUPABASE STORAGE CLEANUP")
    print("=" * 60)
    print()
    
    for bucket in BUCKETS_TO_CLEAR:
        clear_bucket(bucket)
        print()
    
    print("=" * 60)
    print("STORAGE CLEANUP COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
