from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings
import tiktoken
import os
import ssl
import os
import certifi
import shutil
import os

# Get the absolute path to your local cache folder
# This forces tiktoken to skip the SSL-verified download entirely
cache_dir = os.path.join(os.getcwd(), "tiktoken_cache")
os.environ["TIKTOKEN_CACHE_DIR"] = cache_dir
print(os.environ.get("TIKTOKEN_CACHE_DIR"))
# This tells the library exactly which file to use for the 'cl100k_base' encoding
def fix_tiktoken():
    # The library expects a specific naming convention in the cache
    # It usually hashes the URL, but we can trick it by placing the file 
    # where it expects to find the blob download.
    
    blob_url = "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
    import hashlib
    
    # Tiktoken uses the SHA1 hash of the URL as the filename in the cache
    cache_filename = hashlib.sha1(blob_url.encode()).hexdigest()
    cache_file_path = os.path.join(cache_dir, cache_filename)
    
    source_file = os.path.join(cache_dir, "cl100k_base.tiktoken")
    
    if os.path.exists(source_file):
        if not os.path.exists(cache_file_path):
            shutil.copyfile(source_file, cache_file_path)
            print(f"✅ Prepared tiktoken cache at: {cache_file_path}")
    else:
        print(f"❌ Error: {source_file} not found in tiktoken_cache folder!")

fix_tiktoken()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Brand Content Helper - GenAI Backend"
)

# Include the centralized API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Brand Content Helper API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)