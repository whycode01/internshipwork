#!/usr/bin/env python3
"""
Startup script for the Questions API
"""
import os
import sys
from pathlib import Path

import uvicorn

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import settings


def main():
    """Main entry point"""
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📁 Storage path: {settings.storage_path}")
    print(f"🌐 Server: http://{settings.host}:{settings.port}")
    print(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🔍 ReDoc: http://{settings.host}:{settings.port}/redoc")
    
    # Check if storage directory exists
    storage_path = Path(settings.storage_path)
    if not storage_path.exists():
        print(f"⚠️  Warning: Storage directory {storage_path} does not exist")
        print(f"💡 Creating storage directory...")
        storage_path.mkdir(parents=True, exist_ok=True)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()
