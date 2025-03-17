#AUTHOR: RAJ MEHTA

import os
import json
from elasticsearch import Elasticsearch

# Elasticsearch connection
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "contracts"

# Processed files directory
PROCESSED_FOLDER = "processed-files"

# Delete and recreate index (to avoid duplicates)
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

es.indices.create(index=INDEX_NAME, body={
    "settings": {"analysis": {"analyzer": {"custom_analyzer": {
        "type": "standard",
        "stopwords": "_english_"
    }}}},
    "mappings": {
        "properties": {
            "file_name": {"type": "keyword"},
            "chunk_id": {"type": "integer"},
            "text": {"type": "text", "analyzer": "custom_analyzer"}
        }
    }
})

def index_documents():
    """Read processed JSON files and index them into Elasticsearch."""
    for json_file in os.listdir(PROCESSED_FOLDER):
        if json_file.endswith(".json"):
            json_path = os.path.join(PROCESSED_FOLDER, json_file)
            
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Index each chunk into Elasticsearch
            for doc in data:
                es.index(index=INDEX_NAME, body=doc)

            print(f"✔ Indexed: {json_file} ({len(data)} chunks)")

# Run indexing
index_documents()
print("✅ All documents indexed successfully in Elasticsearch!")
