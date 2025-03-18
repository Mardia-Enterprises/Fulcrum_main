"""
OpenAI RAG Processor for Vector Search Results
-------------------------------------------------------------------------------
This module provides integration with OpenAI's language models to enhance
vector search results with various post-processing capabilities:

1. Summarization: Provides concise summaries of search results
2. Analysis: Provides insights and patterns from search results
3. Explanation: Explains concepts mentioned in search results
4. Detail extraction: Extracts comprehensive details from search results
5. Person information extraction: Extracts information about specific individuals

The module is designed for production use with robust error handling, logging,
and performance considerations.
"""

import os
import logging
import sys
import time
from typing import List, Dict, Any, Optional, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("openai_processor")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not installed. Using system environment variables.")

# Import OpenAI with error handling
try:
    import openai
    from openai import OpenAI
    from openai.types.chat import ChatCompletion
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not found. Install with: pip install openai>=1.0.0")
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

class OpenAIProcessor:
    """
    Process vector search results with OpenAI to provide enhanced information retrieval.
    
    This processor adds a RAG (Retrieval-Augmented Generation) layer on top of
    vector search results, allowing for summarization, analysis, explanation,
    and information extraction from retrieved documents.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        temperature: float = 0.5,
        max_tokens: int = 1000
    ):
        """
        Initialize the OpenAI processor.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use for processing
            max_retries: Maximum number of retries for API calls
            retry_delay: Base delay between retries (in seconds)
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        # Get API key from environment variables if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        
        # Initialize client if API key is available
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available. RAG capabilities will be limited.")
            return
            
        if not self.api_key:
            logger.warning("OpenAI API key not provided and not found in environment variables")
            return
            
        try:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAIProcessor with model: {model}")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
    
    def is_person_query(self, query: str) -> bool:
        """
        Determine if a query is asking about a specific person.
        
        This method uses keyword matching to detect queries about people.
        
        Args:
            query: The search query
            
        Returns:
            True if the query is about a person, False otherwise
        """
        # Person-related keywords for detection
        person_keywords = [
            "who is", "worked on", "projects by", "person", "employee", 
            "staff", "personnel", "team member", "colleague", "manager",
            "engineer", "supervisor", "lead", "director", "worked with",
            "responsible for", "involvement", "contribution", "role of"
        ]
        
        # Convert to lowercase for case-insensitive matching
        lower_query = query.lower()
        return any(keyword in lower_query for keyword in person_keywords)
    
    def extract_person_name(self, query: str) -> Optional[str]:
        """
        Extract a person's name from the query.
        
        This method attempts to identify a person's name in the query text.
        It uses OpenAI if available, with a fallback to heuristic extraction.
        
        Args:
            query: The search query string
            
        Returns:
            The extracted person name if found, None otherwise
        """
        # Use simpler extraction if OpenAI is not available
        if not self.client:
            return self._extract_person_name_heuristic(query)
        
        # Use OpenAI for name extraction
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract only the full name of the person being asked about in the query. Respond with only the name, nothing else. If no specific person is mentioned, respond with 'NONE'."},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,  # Use deterministic output
                max_tokens=50,    # Name should be very short
            )
            
            name = response.choices[0].message.content.strip()
            return None if name == 'NONE' else name
            
        except Exception as e:
            logger.error(f"Error extracting person name with OpenAI: {str(e)}")
            # Fall back to heuristic method if OpenAI fails
            return self._extract_person_name_heuristic(query)
    
    def _extract_person_name_heuristic(self, query: str) -> Optional[str]:
        """
        Extract a person's name using simple heuristics.
        
        This is a fallback method when OpenAI is unavailable.
        
        Args:
            query: The search query
            
        Returns:
            The extracted person name if found, None otherwise
        """
        words = query.split()
        
        # Look for consecutive capitalized words (likely a full name)
        for i in range(len(words)-1):
            if (len(words[i]) > 0 and len(words[i+1]) > 0 and 
                words[i][0].isupper() and words[i+1][0].isupper()):
                return f"{words[i]} {words[i+1]}"
        
        # Look for single capitalized words that might be names
        for word in words:
            if (len(word) > 2 and word[0].isupper() and 
                word.lower() not in ["who", "what", "give", "list", "show", "tell", "find"]):
                return word
        
        return None
    
    def summarize_search_results(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]],
        mode: str = "summarize"
    ) -> Dict[str, Any]:
        """
        Process search results using OpenAI.
        
        This method enhances vector search results using OpenAI's language
        models to provide more structured and informative responses.
        
        Args:
            query: Original search query
            search_results: List of search results from vector search
            mode: Processing mode (summarize, analyze, explain, detail, person)
                - summarize: Provide a concise summary of the search results
                - analyze: Analyze the information and provide insights
                - explain: Explain the concepts mentioned in the results
                - detail: Provide detailed information based on the results
                - person: Extract information about a specific person
            
        Returns:
            Dictionary with processed results
        """
        # Handle case when OpenAI is not available
        if not self.client:
            return {
                "error": "OpenAI client not initialized. Please check your API key.",
                "original_results": search_results
            }
        
        # Handle empty search results
        if not search_results:
            return {
                "summary": "No search results found for your query.",
                "query": query,
                "original_results": []
            }
        
        # Auto-detect if this is a person query
        is_person_query = self.is_person_query(query)
        person_name = self.extract_person_name(query) if is_person_query else None
        
        # If this is a person query but no mode was specified, set to "person"
        if is_person_query and mode == "summarize":
            mode = "person"
            logger.info(f"Auto-detected person query for '{person_name}'. Using 'person' mode.")
        
        # Prepare content and prompts
        content = self._prepare_content_from_results(search_results)
        system_message = self._get_system_message(mode, person_name)
        user_message = self._prepare_user_message(query, content, mode, person_name)
        
        # Process with OpenAI
        try:
            return self._call_openai_with_retry(query, search_results, person_name, system_message, user_message, mode)
        except Exception as e:
            logger.error(f"Error processing with OpenAI: {str(e)}")
            return {
                "error": f"Error processing with OpenAI: {str(e)}",
                "query": query,
                "original_results": search_results
            }
    
    def _call_openai_with_retry(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        person_name: Optional[str],
        system_message: str,
        user_message: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with retry logic for robustness.
        
        Args:
            query: Original search query
            search_results: List of search results
            person_name: Extracted person name (if applicable)
            system_message: System prompt for OpenAI
            user_message: User prompt for OpenAI
            mode: Processing mode
            
        Returns:
            Processed results dictionary
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                
                # Extract response
                processed_text = response.choices[0].message.content
                
                return {
                    "query": query,
                    "mode": mode,
                    "processed_result": processed_text,
                    "model_used": self.model,
                    "person_name": person_name if person_name else None,
                    "original_results": search_results
                }
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Log the error
                logger.warning(f"OpenAI API call failed (attempt {retry_count}/{self.max_retries}): {str(e)}")
                
                # Exponential backoff
                if retry_count < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
        
        # If we've exhausted retries, raise the last error
        logger.error(f"OpenAI API call failed after {self.max_retries} attempts: {str(last_error)}")
        raise last_error
    
    def _prepare_content_from_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results for inclusion in OpenAI prompts.
        
        Args:
            search_results: List of search results from vector search
            
        Returns:
            Formatted content string
        """
        content_parts = []
        
        for i, result in enumerate(search_results):
            document = result.get("metadata", {}).get("filename", "Unknown document")
            text = result.get("text", "")
            score = result.get("score", 0)
            
            content_parts.append(f"Document {i+1}: {document} (Relevance: {score:.4f})")
            content_parts.append(f"Content: {text}")
            content_parts.append("---")
        
        return "\n".join(content_parts)
    
    def _prepare_user_message(
        self, 
        query: str, 
        content: str, 
        mode: str, 
        person_name: Optional[str] = None
    ) -> str:
        """
        Create the user message for OpenAI based on query type and mode.
        
        Args:
            query: Original search query
            content: Formatted content from search results
            mode: Processing mode
            person_name: Extracted person name (if applicable)
            
        Returns:
            Formatted user message
        """
        base_message = f"""Query: {query}

Content from search results:
{content}

Please {mode} this information in relation to the query."""

        # Add special instructions for person queries
        if mode == "person" and person_name:
            base_message += f"""

Extract all projects and work that {person_name} has been involved with. Organize by project.
Focus on:
1. Project names and identifiers
2. Their role in each project
3. Responsibilities and contributions
4. Timeline information if available"""

        return base_message
    
    def _get_system_message(self, mode: str, person_name: Optional[str] = None) -> str:
        """
        Generate the appropriate system message based on processing mode.
        
        Args:
            mode: Processing mode
            person_name: Name of the person for person queries
            
        Returns:
            System message for OpenAI prompt
        """
        if mode == "summarize":
            return """You are an AI assistant that provides concise summaries of information.
Given search results from a document database, create a clear, well-structured summary that captures the key points 
relevant to the user's query. Be factual and objective, focusing only on information present in the documents.
Format your summary with clear sections and bullet points where appropriate."""
            
        elif mode == "analyze":
            return """You are an AI assistant that analyzes information deeply.
Given search results from a document database, provide a thoughtful analysis that identifies patterns, implications, 
and insights relevant to the user's query. Connect concepts across different documents and highlight important 
relationships. Structure your analysis with clear sections addressing different aspects of the query."""
            
        elif mode == "explain":
            return """You are an AI assistant that explains complex information clearly.
Given search results from a document database, provide an educational explanation of the concepts mentioned
that relate to the user's query. Define terminology, explain relationships between concepts, and provide 
background context where helpful. Your explanation should be accessible to someone without specialist knowledge."""
            
        elif mode == "detail":
            return """You are an AI assistant that provides comprehensive, detailed information.
Given search results from a document database, extract and organize all relevant details that address the 
user's query. Be thorough and precise, citing specific information from each document. Structure your response 
with clear sections and subsections to cover all aspects of the query in depth."""

        elif mode == "person":
            prompt = """You are an AI assistant that extracts information about specific people from documents.
Given search results from a document database, extract all information related to the person mentioned in the query.
Focus on identifying projects they've worked on, their role in each project, their expertise, and any other relevant details.
Format your response as a structured profile with clear sections for:
1. Projects Involved In (list each project with details)
2. Roles and Responsibilities 
3. Areas of Expertise
4. Other Relevant Information

Be concise but thorough. Only include information that is clearly stated in the documents. 
If a document filename contains information about a project, consider that in your analysis.
If certain information is not available in the documents, state this clearly rather than fabricating details."""

            # Add person name if available
            if person_name:
                prompt += f"\n\nThe person you need to extract information about is: {person_name}"
                
            return prompt
            
        else:
            return """You are an AI assistant that helps extract and organize information from document search results.
Provide a helpful response based on the content of the documents and the user's query.
Focus only on the information present in the documents and avoid making assumptions or adding details not present in the content."""


def process_rag_results(
    query: str,
    search_results: List[Dict[str, Any]],
    mode: str = "summarize",
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """
    Process search results with OpenAI (convenience function).
    
    This function provides a simple interface to the OpenAIProcessor
    for quick integration into applications.
    
    Args:
        query: Original search query
        search_results: List of search results from vector search
        mode: Processing mode (summarize, analyze, explain, detail, person)
        api_key: OpenAI API key
        model: OpenAI model to use
        
    Returns:
        Processed results dictionary
    """
    processor = OpenAIProcessor(api_key=api_key, model=model)
    return processor.summarize_search_results(query, search_results, mode)


if __name__ == "__main__":
    # Example usage
    example_results = [
        {
            "id": "doc1_0",
            "score": 0.85,
            "text": "Vector search uses embeddings to find semantically similar documents.",
            "metadata": {"filename": "vector_search.pdf"}
        },
        {
            "id": "doc2_1",
            "score": 0.75,
            "text": "RAG (Retrieval-Augmented Generation) combines retrieval systems with generative AI.",
            "metadata": {"filename": "rag_systems.pdf"}
        }
    ]
    
    processor = OpenAIProcessor()
    result = processor.summarize_search_results(
        query="How does vector search work with RAG?",
        search_results=example_results,
        mode="explain"
    )
    
    print(json.dumps(result, indent=2)) 