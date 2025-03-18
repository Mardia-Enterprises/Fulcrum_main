"""
OpenAI Processor for document summarization and analysis.
This module integrates OpenAI's language models with the vector search results
to provide enhanced information retrieval capabilities.
"""

import os
import logging
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Import OpenAI
try:
    import openai
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI package not found. Install with: pip install openai")
    openai = None
    OpenAI = None

class OpenAIProcessor:
    """
    Process vector search results with OpenAI to provide enhanced information.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize the OpenAI processor.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        # Get API key from environment variables if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided and not found in environment variables")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.model = model
                logger.info(f"Initialized OpenAIProcessor with model: {model}")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
                self.client = None
    
    def is_person_query(self, query: str) -> bool:
        """
        Check if the query is asking about a specific person.
        
        Args:
            query: The search query
            
        Returns:
            True if the query is about a person, False otherwise
        """
        # Simple keyword check - could be enhanced with NLP
        person_keywords = [
            "who is", "worked on", "projects by", "person", "employee", 
            "staff", "personnel", "team member", "colleague", "manager",
            "engineer", "supervisor", "lead", "director", "worked with"
        ]
        
        lower_query = query.lower()
        return any(keyword in lower_query for keyword in person_keywords)
    
    def extract_person_name(self, query: str) -> Optional[str]:
        """
        Extract a person's name from the query.
        
        Args:
            query: The search query
            
        Returns:
            The extracted person name if found, None otherwise
        """
        if not self.client:
            # Simple fallback if OpenAI client not available
            words = query.split()
            for i in range(len(words)-1):
                # Simple heuristic: look for consecutive capitalized words
                if words[i][0].isupper() and words[i+1][0].isupper():
                    return f"{words[i]} {words[i+1]}"
            
            # Look for single capitalized words that might be names
            for word in words:
                if word[0].isupper() and len(word) > 2 and word.lower() not in ["who", "what", "give", "list", "show", "tell", "find"]:
                    return word
            
            return None
        
        try:
            # Use OpenAI to extract the person name
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract only the full name of the person being asked about in the query. Respond with only the name, nothing else. If no specific person is mentioned, respond with 'NONE'."},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=50,
            )
            
            name = response.choices[0].message.content.strip()
            return None if name == 'NONE' else name
            
        except Exception as e:
            logger.error(f"Error extracting person name: {str(e)}")
            return None
    
    def summarize_search_results(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]],
        mode: str = "summarize"
    ) -> Dict[str, Any]:
        """
        Summarize search results using OpenAI.
        
        Args:
            query: Original search query
            search_results: List of search results from vector search
            mode: Processing mode (summarize, analyze, explain, or detail)
                - summarize: Provide a concise summary of the search results
                - analyze: Analyze the information and provide insights
                - explain: Explain the concepts mentioned in the results
                - detail: Provide detailed information based on the results
                - projects: Specifically extract project information
                - person: Extract information about a specific person
            
        Returns:
            Dictionary with processed results
        """
        if not self.client:
            return {
                "error": "OpenAI client not initialized. Please check your API key.",
                "original_results": search_results
            }
        
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
        
        # Prepare content from search results
        content = self._prepare_content_from_results(search_results)
        
        # Prepare system message based on mode
        system_message = self._get_system_message(mode, person_name)
        
        # Prepare user message
        user_message = f"""Query: {query}

Content from search results:
{content}

Please {mode} this information in relation to the query."""

        if mode == "person" and person_name:
            user_message += f"\n\nExtract all projects and work that {person_name} has been involved with. Organize by project."
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            
            # Extract response
            processed_text = response.choices[0].message.content
            
            return {
                "query": query,
                "mode": mode,
                "processed_result": processed_text,
                "model_used": self.model,
                "person_name": person_name if is_person_query else None,
                "original_results": search_results
            }
            
        except Exception as e:
            logger.error(f"Error processing with OpenAI: {str(e)}")
            return {
                "error": f"Error processing with OpenAI: {str(e)}",
                "query": query,
                "original_results": search_results
            }
    
    def _prepare_content_from_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Prepare content from search results for the OpenAI prompt.
        
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
    
    def _get_system_message(self, mode: str, person_name: Optional[str] = None) -> str:
        """
        Get the appropriate system message based on the processing mode.
        
        Args:
            mode: Processing mode (summarize, analyze, explain, or detail)
            person_name: Name of the person if this is a person query
            
        Returns:
            System message for OpenAI
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

Be concise but thorough. Only include information that is clearly stated in the documents. If a document filename contains information about a project, make sure to include that in your analysis."""

            if person_name:
                prompt += f"\n\nThe person you need to extract information about is: {person_name}"
                
            return prompt
            
        else:
            return """You are an AI assistant that helps extract and organize information from document search results.
Provide a helpful response based on the content of the documents and the user's query."""

def process_rag_results(
    query: str,
    search_results: List[Dict[str, Any]],
    mode: str = "summarize",
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """
    Process search results with OpenAI (convenience function).
    
    Args:
        query: Original search query
        search_results: List of search results from vector search
        mode: Processing mode (summarize, analyze, explain, or detail)
        api_key: OpenAI API key
        model: OpenAI model to use
        
    Returns:
        Processed results
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