#!/usr/bin/env python3
"""
Script to download NLTK data with SSL certificate verification disabled.
This is useful for environments where SSL certificate verification fails.
"""

import ssl
import nltk
import sys

print("Downloading NLTK data with SSL certificate verification disabled...")

try:
    # Create unverified SSL context
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # Download punkt tokenizer
    nltk.download('punkt')
    print("✅ Successfully downloaded punkt tokenizer.")
    
    # Verify it was downloaded
    nltk.data.find('tokenizers/punkt')
    print("✅ Verified punkt tokenizer is available.")
    
    sys.exit(0)
except Exception as e:
    print(f"❌ Error downloading NLTK data: {str(e)}")
    
    # Try to create the directory manually
    import os
    from pathlib import Path
    
    try:
        # Create NLTK data directory
        nltk_data_dir = os.path.expanduser("~/nltk_data/tokenizers")
        os.makedirs(nltk_data_dir, exist_ok=True)
        print(f"Created NLTK data directory: {nltk_data_dir}")
        
        # Check if we can find the punkt tokenizer now
        try:
            nltk.data.find('tokenizers/punkt')
            print("✅ Found punkt tokenizer after creating directory.")
            sys.exit(0)
        except LookupError:
            print("Still couldn't find punkt tokenizer.")
            
            # Last resort: try to get it from a different source or create a stub
            print("Creating a stub punkt tokenizer to avoid further errors...")
            
            punkt_path = os.path.join(nltk_data_dir, "punkt")
            if not os.path.exists(punkt_path):
                os.makedirs(punkt_path, exist_ok=True)
            
            with open(os.path.join(punkt_path, "README"), 'w') as f:
                f.write("This is a stub to avoid NLTK download errors.\n")
            
            print("Created a stub punkt tokenizer.")
            print("⚠️ Warning: Some functionality may be limited without the proper NLTK data.")
            sys.exit(1)
    except Exception as e2:
        print(f"❌ Failed to create directory manually: {str(e2)}")
        sys.exit(1) 