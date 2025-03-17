import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Now import and run the API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("API.main:app", host="0.0.0.0", port=8080, reload=True) 