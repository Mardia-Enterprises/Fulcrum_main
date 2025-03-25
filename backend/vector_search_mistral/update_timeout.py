import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")

if not supabase_url or not supabase_key:
    logger.error("Missing Supabase credentials in environment variables")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def update_function_timeout():
    """Update functions with a 45-second timeout, renaming to avoid conflicts."""
    try:
        # SQL to recreate the function with a new name
        sql = """
        -- Drop existing functions (in case they exist)
        DROP FUNCTION IF EXISTS match_documents(VECTOR(1024), FLOAT, INT);
        DROP FUNCTION IF EXISTS match_documents(VECTOR(1024), FLOAT, INT, TEXT);
        
        -- Create primary function (without filter)
        CREATE OR REPLACE FUNCTION match_documents(
          query_embedding VECTOR(1024),
          match_threshold FLOAT,
          match_count INT
        )
        RETURNS TABLE (
          id TEXT,
          content TEXT,
          metadata JSONB,
          file_path TEXT,
          chunk_id TEXT,
          file_type TEXT,
          similarity FLOAT
        )
        LANGUAGE plpgsql
        SET statement_timeout = '45s'
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            pdf_documents.id,
            pdf_documents.content,
            pdf_documents.metadata,
            pdf_documents.file_path,
            pdf_documents.chunk_id,
            pdf_documents.file_type,
            1 - (pdf_documents.embedding <=> query_embedding) AS similarity
          FROM pdf_documents
          WHERE 1 - (pdf_documents.embedding <=> query_embedding) > match_threshold
          ORDER BY similarity DESC
          LIMIT match_count;
        END;
        $$;

        -- Create filtered version with different name
        CREATE OR REPLACE FUNCTION match_documents_filtered(
          query_embedding VECTOR(1024),
          match_threshold FLOAT,
          match_count INT,
          filter_string TEXT
        )
        RETURNS TABLE (
          id TEXT,
          content TEXT,
          metadata JSONB,
          file_path TEXT,
          chunk_id TEXT,
          file_type TEXT,
          similarity FLOAT
        )
        LANGUAGE plpgsql
        SET statement_timeout = '45s'
        AS $$
        BEGIN
          IF filter_string IS NULL THEN
            RETURN QUERY
            SELECT * FROM match_documents(query_embedding, match_threshold, match_count);
          ELSE
            RETURN QUERY EXECUTE
            format('
              SELECT
                pdf_documents.id,
                pdf_documents.content,
                pdf_documents.metadata,
                pdf_documents.file_path,
                pdf_documents.chunk_id,
                pdf_documents.file_type,
                1 - (pdf_documents.embedding <=> %L::vector) AS similarity
              FROM pdf_documents
              WHERE 
                1 - (pdf_documents.embedding <=> %L::vector) > %s
                AND %s
              ORDER BY similarity DESC
              LIMIT %s
            ', query_embedding, query_embedding, match_threshold, filter_string, match_count);
          END IF;
        END;
        $$;
        """
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error updating functions: {result.error}")
        else:
            logger.info("Successfully updated functions with 45-second timeout")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    update_function_timeout() 