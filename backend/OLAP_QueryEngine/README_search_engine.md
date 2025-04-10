# Database Search Engine

This search engine allows you to query information about teams, projects, and their relationships from your Supabase database using natural language. It uses OpenAI's GPT-4o model to understand queries and generate helpful responses based on the database content.

## Features

- **Natural Language Queries**: Ask questions about teams, projects, and their relationships in plain English
- **Semantic Search**: Uses embeddings for finding semantically relevant content
- **Text Chunk Focused**: Searches specific relevant text chunks in `public.sharded_documents` based on text_ids rather than entire documents
- **Comprehensive Results**: Retrieves information from multiple related tables to provide complete answers
- **Document Retrieval**: Finds and includes relevant text chunks in the responses with their source information
- **Source Attribution**: Every response includes the complete text chunks from source documents with their text_ids and document links
- **Graceful Fallbacks**: Falls back to simpler search methods if vector search is not available
- **Optimized Queries**: Special handling for common query patterns to provide more detailed responses

## Setup

1. Ensure you have the required Python packages installed:

```bash
pip install openai supabase python-dotenv
```

2. Make sure your `.env` file includes the necessary credentials:

```
# Supabase Configuration
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

3. **Important**: Before using the search engine, you need to run the SQL functions in `schema/vector_search_functions.sql` in your Supabase database to enable vector search capability. This can be done via the Supabase SQL Editor.

   ```sql
   -- Execute the SQL in vector_search_functions.sql in your Supabase SQL Editor
   ```

   Note: The search engine will still work without these functions, but it will use simpler text-based search methods instead of semantic search.

4. Make sure your embedding dimensions match. If you're using OpenAI's embedding model (text-embedding-3-small), your vector column should be configured for 1536 dimensions. If using a different model, adjust the dimensions accordingly.

## Usage

You can use the search engine from the command line by running:

```bash
python search_engine.py "your query here"
```

Example queries:

```bash
python search_engine.py "Who are the engineers on the team?"
python search_engine.py "What projects are civil engineers working on?"
python search_engine.py "Tell me about drainage projects in Texas"
```

For a comprehensive demonstration of various query types and features, run the demo script:

```bash
python demo_search.py
```

## Response Format

Each search response includes:

1. A clear, concise answer to your query with all relevant information
2. Project details including location, role, and descriptions when applicable
3. A "RELEVANT TEXT CHUNKS" section that includes:
   - Full text of the most relevant text chunks (not entire documents)
   - Text IDs for precise reference to specific content
   - Document links to source PDFs in Supabase storage

This format ensures you not only get the answer to your query but also the specific text chunks and their source information.

## How It Works

1. The search engine analyzes your query using OpenAI to determine what kind of information you're looking for
2. Based on the query type, it searches the appropriate tables in the database
3. For team or project searches, it retrieves related information (projects for teams, teams for projects)
4. It identifies and collects specific text_ids relevant to the query
5. It retrieves only the relevant text chunks from `public.sharded_documents` based on these text_ids
6. For semantic search, it directly queries text chunks by similarity, not entire documents
7. It performs semantic search using vector embeddings to find relevant text chunks (if vector search functions are available)
8. The search results are passed to OpenAI's GPT-4o to generate a natural language response
9. Text chunks and source links are added to each response to provide full context and traceability

## Optimized Query Patterns

The search engine includes special optimizations for certain common query patterns:

1. **Team Member Project Queries**: Queries like "What projects are civil engineers working on?" are specially handled to provide comprehensive information about team members' projects with detailed descriptions from related text chunks.

2. **Project Information Queries**: When asking about specific projects like "What drainage projects are there?", the engine performs partial matching on project names and locations to find relevant information even with incomplete names.

3. **Fallback OpenAI Handling**: If OpenAI's API experiences rate limits or other issues, the engine includes fallback response generators that can still provide useful information from the database search results.

## Query Types

The engine can handle various types of queries:

- **Team Information**: Questions about specific teams or individuals
- **Project Information**: Questions about specific projects
- **Team Projects**: Questions about what projects a team has worked on
- **Project Teams**: Questions about what teams worked on a project
- **General Queries**: Broader questions that may involve multiple entities

## Database Schema

The search engine works with the following tables:

- `teams`: Information about teams/employees
- `projects`: Information about projects
- `team_projects`: Links teams to projects and contains relevant text_ids
- `documents`: Original document metadata and links
- `sharded_documents`: Text chunks from documents with embeddings (the search focuses here)

## Text Chunk Focus

The key improvement in this search engine is its focus on specific text chunks rather than entire documents:

1. **Targeted Search**: The engine identifies and searches for specific text chunks in `public.sharded_documents` based on relevant text_ids.
2. **Precision**: Each search targets only the text chunks directly relevant to your query rather than entire documents.
3. **Efficiency**: By focusing on specific text chunks, the search is more efficient and precise.
4. **Relevant Results**: The responses include only the most relevant text chunks with their specific text_ids and document links.

## Extending the Search Engine

To add support for more query types or database tables:

1. Add new functions for querying additional tables
2. Extend the `analyze_query` function to recognize new query types
3. Update the `execute_search` function to handle the new query types
4. Modify the `generate_response` system prompt to include the new data types

## Troubleshooting

- **Supabase Connection Issues**: Verify your Supabase URL and API key in the `.env` file
- **OpenAI API Issues**: Check your OpenAI API key and ensure you have sufficient credits
- **Vector Search Errors**: Make sure you've run the SQL functions in your Supabase database. If you get dimension mismatch errors, ensure your embedding dimensions match your vector column configuration.
- **Missing Results**: Ensure your database tables contain the relevant data and that the text chunks have embeddings
- **SQL Function Missing**: If you see errors about missing SQL functions, make sure you've executed the SQL in `schema/vector_search_functions.sql` in your Supabase SQL Editor 