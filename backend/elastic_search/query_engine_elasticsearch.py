from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "contracts"

def search_documents(query_text):
    """Search for documents in Elasticsearch based on the query text."""
    query = {
        "query": {
            "match": {
                "text": query_text
            }
        },
        "highlight": {
            "fields": {
                "text": {}
            }
        }
    }

    response = es.search(index=INDEX_NAME, body=query)

    results = []
    for hit in response['hits']['hits']:
        results.append({
            "file_name": hit['_source']['file_name'],
            "chunk_id": hit['_source']['chunk_id'],
            "highlight": hit['highlight']['text'] if "highlight" in hit else hit['_source']['text'][:300]
        })
    
    return results

if __name__ == "__main__":
    query_text = input("Enter search query: ")
    results = search_documents(query_text)
    
    for res in results:
        print(f"📄 File: {res['file_name']} - Chunk {res['chunk_id']}")
        print(f"🔎 Snippet: {res['highlight']}")
        print("-" * 50)
