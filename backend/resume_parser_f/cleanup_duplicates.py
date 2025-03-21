#!/usr/bin/env python3
"""
Script to identify and clean up duplicate projects in the Supabase database.
This script will find projects with similar titles, merge their data, and delete the duplicates.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - \033[1;33m%(levelname)s\033[0m - %(message)s',
    handlers=[
        logging.FileHandler("resume_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

def check_environment() -> bool:
    """
    Check that all required environment variables are set.
    
    Returns:
        True if all environment variables are set, False otherwise
    """
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    if not supabase_url or not supabase_key:
        logger.error("\033[91mError: Supabase credentials not found in .env file\033[0m")
        logger.error("Please add your Supabase URL and API key to the .env file in the root directory")
        return False

    # Check for OpenAI API key (needed for embeddings)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("\033[91mError: OPENAI_API_KEY not found in .env file\033[0m")
        logger.error("Please add your OpenAI API key to the .env file in the root directory")
        return False
    
    return True

def normalize_title(title: str) -> str:
    """
    Normalize a title for comparison to detect duplicates.
    
    Args:
        title: Project title
        
    Returns:
        Normalized title for comparison
    """
    if not isinstance(title, str):
        title = str(title)
    return title.lower().replace(" ", "").replace(",", "").replace(".", "").replace("-", "").replace("_", "")

def find_duplicate_projects() -> List[List[Dict[str, Any]]]:
    """
    Find groups of duplicate projects in Supabase based on title similarity.
    
    Returns:
        List of lists, where each inner list contains duplicate projects
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_PROJECT_URL")
        supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get all projects
        logger.info("Fetching all projects from Supabase...")
        result = supabase.table('projects').select('id, title, project_data, created_at').execute()
        
        if not result.data:
            logger.info("No projects found in Supabase")
            return []
        
        projects = result.data
        logger.info(f"Found {len(projects)} projects in Supabase")
        
        # Create lookup for normalized titles
        duplicates = []
        processed_ids = set()
        
        for i, project in enumerate(projects):
            if project.get('id') in processed_ids:
                continue
                
            title = project.get('title', '')
            if not title:
                continue
                
            normalized_title = normalize_title(title)
            duplicate_group = [project]
            
            # Find all duplicates of this project
            for j, other_project in enumerate(projects):
                if i == j or other_project.get('id') in processed_ids:
                    continue
                    
                other_title = other_project.get('title', '')
                if not other_title:
                    continue
                    
                other_normalized = normalize_title(other_title)
                
                # Check for title similarity
                if (normalized_title in other_normalized or 
                    other_normalized in normalized_title or
                    (len(normalized_title) > 10 and len(other_normalized) > 10 and 
                     (normalized_title[:10] == other_normalized[:10] or 
                      normalized_title[-10:] == other_normalized[-10:]))):
                    duplicate_group.append(other_project)
                    processed_ids.add(other_project.get('id'))
            
            # If we found duplicates, add this group
            if len(duplicate_group) > 1:
                processed_ids.add(project.get('id'))
                duplicates.append(duplicate_group)
        
        logger.info(f"Found {len(duplicates)} groups of duplicate projects")
        for i, group in enumerate(duplicates):
            logger.info(f"Group {i+1}: {len(group)} duplicates of '{group[0].get('title')}'")
        
        return duplicates
        
    except Exception as e:
        logger.error(f"\033[91mError finding duplicate projects: {str(e)}\033[0m")
        return []

def merge_project_data(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge data from multiple projects, keeping the most complete information.
    
    Args:
        projects: List of projects to merge
        
    Returns:
        Merged project data
    """
    # Sort projects by creation date, most recent first
    sorted_projects = sorted(projects, key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Start with the most recent project as base
    merged_data = sorted_projects[0]
    merged_project_data = merged_data.get('project_data', {}).copy()
    
    # Merge in data from other projects
    for project in sorted_projects[1:]:
        project_data = project.get('project_data', {})
        if not project_data:
            continue
            
        for key, value in project_data.items():
            # If the key doesn't exist in merged data or has an empty value, use this value
            if key not in merged_project_data or not merged_project_data[key]:
                merged_project_data[key] = value
    
    merged_data['project_data'] = merged_project_data
    return merged_data

def clean_up_duplicates(dry_run: bool = False) -> bool:
    """
    Clean up duplicate projects by merging their data and deleting the duplicates.
    
    Args:
        dry_run: If True, only show what would be done without making changes
        
    Returns:
        True if the cleanup was successful, False otherwise
    """
    if not check_environment():
        return False
    
    # Import required modules
    try:
        from openai import OpenAI
        from supabase import create_client
        from datauploader import generate_embedding, project_to_text
    except ImportError as e:
        logger.error(f"\033[91mError importing required modules: {str(e)}\033[0m")
        logger.error("\033[93mPlease run './install_dependencies.sh' to install required packages\033[0m")
        return False
    
    # Initialize clients
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_api_key)
    
    # Find duplicate projects
    duplicate_groups = find_duplicate_projects()
    
    if not duplicate_groups:
        logger.info("No duplicates found, nothing to clean up")
        return True
    
    if dry_run:
        logger.info("\033[93mDRY RUN: No changes will be made\033[0m")
    
    # Process each group of duplicates
    for i, group in enumerate(duplicate_groups):
        logger.info(f"\nProcessing duplicate group {i+1}/{len(duplicate_groups)}")
        
        # Merge the data from all duplicates
        merged = merge_project_data(group)
        primary_id = merged.get('id')
        primary_title = merged.get('title')
        
        logger.info(f"Primary project: {primary_title} (ID: {primary_id})")
        
        # Generate text for embedding
        project_text = project_to_text(merged.get('project_data', {}))
        
        # Generate new embedding
        if not dry_run:
            try:
                # Generate embedding with OpenAI
                response = openai_client.embeddings.create(
                    input=project_text,
                    model="text-embedding-3-small"
                )
                
                embedding = response.data[0].embedding
                
                # Update the primary project with merged data and new embedding
                update_data = {
                    "title": primary_title,
                    "project_data": merged.get('project_data', {}),
                    "embedding": embedding
                }
                
                result = supabase.table('projects').update(update_data).eq('id', primary_id).execute()
                logger.info(f"\033[92m✓ Updated primary project: {primary_id}\033[0m")
                
                # Delete the duplicates
                for project in group:
                    if project.get('id') != primary_id:
                        duplicate_id = project.get('id')
                        result = supabase.table('projects').delete().eq('id', duplicate_id).execute()
                        logger.info(f"\033[92m✓ Deleted duplicate: {duplicate_id}\033[0m")
                
            except Exception as e:
                logger.error(f"\033[91mError processing duplicate group: {str(e)}\033[0m")
                continue
        else:
            # In dry run mode, just log what would be done
            logger.info("\033[93mWould update primary project with merged data\033[0m")
            for project in group:
                if project.get('id') != primary_id:
                    logger.info(f"\033[93mWould delete duplicate: {project.get('id')}\033[0m")
    
    return True

if __name__ == "__main__":
    print("\n\033[1;36m===== Supabase Project Duplicate Cleanup =====\033[0m")
    print("This script will identify and clean up duplicate projects in the Supabase database.")
    print("\nOptions:")
    print("  1. Dry run (show what would be done without making changes)")
    print("  2. Execute cleanup (WARNING: This will delete duplicate projects)")
    print("  q. Quit")
    
    choice = input("\nEnter your choice (1/2/q): ")
    
    if choice == '1':
        clean_up_duplicates(dry_run=True)
    elif choice == '2':
        confirm = input("\n\033[93mWARNING: This will merge and delete duplicate projects in Supabase.\033[0m\nAre you sure you want to continue? (y/n): ")
        if confirm.lower() == 'y':
            clean_up_duplicates(dry_run=False)
        else:
            print("Cleanup cancelled.")
    else:
        print("Exiting without changes.") 