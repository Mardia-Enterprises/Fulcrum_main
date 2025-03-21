#!/bin/bash

# Script to process both PDF types and update Supabase
# Handles both Section E and Section F PDFs

# Set text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}=== PDF Processor for Sections E and F ===${NC}"

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    echo -e "${BLUE}Activating virtual environment from project root...${NC}"
    source ../.venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Using system Python.${NC}"
    echo -e "${YELLOW}It's recommended to create a virtual environment.${NC}"
fi

# Check if we have required environment variables
function check_env_var {
    local var_name=$1
    if [ -z "${!var_name}" ]; then
        # Try to load from .env file
        if [ -f "../.env" ]; then
            source <(grep -v '^#' ../.env | sed -E 's/(.*)=(.*)$/export \1="\2"/g')
        fi
        
        # Check again
        if [ -z "${!var_name}" ]; then
            echo -e "${RED}Error: $var_name environment variable not set${NC}"
            echo -e "${YELLOW}Please set this in your .env file${NC}"
            return 1
        fi
    fi
    return 0
}

# Check required environment variables
echo -e "${BLUE}Checking environment variables...${NC}"
check_env_var "MISTRAL_API_KEY" || exit 1
check_env_var "OPENAI_API_KEY" || exit 1
check_env_var "SUPABASE_PROJECT_URL" || exit 1
check_env_var "SUPABASE_PRIVATE_API_KEY" || exit 1

echo -e "${GREEN}✓ Environment variables found${NC}"

# Create required directories if they don't exist
echo -e "${BLUE}Creating required directories...${NC}"
mkdir -p resume_parser/output
mkdir -p resume_parser_f/output
mkdir -p resume_parser_f/debug

# Function to process Section E resumes
function process_section_e() {
    echo -e "\n${BLUE}${BOLD}=== Processing Section E Resumes ===${NC}"
    
    # Define PDF directory for Section E
    SECTION_E_DIR="Section E Resumes"
    
    # Check if the PDF directory exists
    if [ ! -d "$SECTION_E_DIR" ]; then
        echo -e "${YELLOW}Warning: Section E Resumes directory not found at $SECTION_E_DIR - skipping${NC}"
        return 0
    fi
    
    # Count the number of PDFs
    NUM_PDFS=$(find "$SECTION_E_DIR" -name "*.pdf" | wc -l)
    if [ "$NUM_PDFS" -eq 0 ]; then
        echo -e "${YELLOW}Warning: No PDF files found in $SECTION_E_DIR - skipping${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Found $NUM_PDFS PDF files to process in Section E${NC}"
    
    # Process PDFs with the resume_parser script
    echo -e "${BLUE}Running Section E processing...${NC}"
    cd resume_parser || { echo -e "${RED}Error: resume_parser directory not found${NC}"; return 1; }
    
    # Run the Python script for processing
    python dataparser.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Section E data parsing failed${NC}"
        cd ..
        return 1
    fi
    
    # Upload the data
    python datauploader.py 
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Section E data upload failed${NC}"
        cd ..
        return 1
    fi
    
    cd ..
    echo -e "${GREEN}${BOLD}✓ Section E processing completed successfully${NC}"
    return 0
}

# Function to process Section F resumes
function process_section_f() {
    echo -e "\n${BLUE}${BOLD}=== Processing Section F Resumes ===${NC}"
    
    # Define PDF directory for Section F
    SECTION_F_DIR="Section F Resumes"
    
    # Check if the PDF directory exists
    if [ ! -d "$SECTION_F_DIR" ]; then
        echo -e "${YELLOW}Warning: Section F Resumes directory not found at $SECTION_F_DIR - skipping${NC}"
        return 0
    fi
    
    # Count the number of PDFs
    NUM_PDFS=$(find "$SECTION_F_DIR" -name "*.pdf" | wc -l)
    if [ "$NUM_PDFS" -eq 0 ]; then
        echo -e "${YELLOW}Warning: No PDF files found in $SECTION_F_DIR - skipping${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Found $NUM_PDFS PDF files to process in Section F${NC}"
    
    # Change to resume_parser_f directory and run processor
    echo -e "${BLUE}Running Section F processing...${NC}"
    cd resume_parser_f || { echo -e "${RED}Error: resume_parser_f directory not found${NC}"; return 1; }
    
    # Run the process script
    ./process_section_f.sh "../$SECTION_F_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Section F processing failed${NC}"
        cd ..
        return 1
    fi
    
    cd ..
    echo -e "${GREEN}${BOLD}✓ Section F processing completed successfully${NC}"
    return 0
}

# Verify uploads function
function verify_uploads() {
    echo -e "\n${BLUE}${BOLD}=== Verifying Uploads ===${NC}"
    
    # Run verification for Section F
    if [ -f "resume_parser_f/verify_uploads.py" ]; then
        echo -e "${BLUE}Verifying Section F uploads...${NC}"
        cd resume_parser_f || { echo -e "${RED}Error: resume_parser_f directory not found${NC}"; return 1; }
        
        python verify_uploads.py
        VERIFY_RESULT=$?
        
        cd ..
        
        if [ $VERIFY_RESULT -ne 0 ]; then
            echo -e "${RED}Error: Section F verification failed${NC}"
            return 1
        fi
        
        echo -e "${GREEN}✓ Section F verification completed${NC}"
    else
        echo -e "${YELLOW}Warning: Section F verification script not found - skipping${NC}"
    fi
    
    # Run verification for Supabase connectivity
    if [ -f "debug_supabase.py" ]; then
        echo -e "${BLUE}Running Supabase diagnostics...${NC}"
        
        python debug_supabase.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Supabase diagnostics failed${NC}"
            return 1
        fi
        
        echo -e "${GREEN}✓ Supabase diagnostics completed${NC}"
    else
        echo -e "${YELLOW}Warning: Supabase diagnostics script not found - skipping${NC}"
    fi
    
    echo -e "${GREEN}${BOLD}✓ Verification completed successfully${NC}"
    return 0
}

# Process command line arguments
SKIP_SECTION_E=false
SKIP_SECTION_F=false
SKIP_VERIFY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-section-e)
      SKIP_SECTION_E=true
      shift
      ;;
    --skip-section-f)
      SKIP_SECTION_F=true
      shift
      ;;
    --skip-verify)
      SKIP_VERIFY=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --skip-section-e   Skip processing Section E resumes"
      echo "  --skip-section-f   Skip processing Section F resumes"
      echo "  --skip-verify      Skip verification steps"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Main execution flow
echo -e "${BLUE}${BOLD}Starting PDF processing...${NC}"

# Process Section E if not skipped
if [ "$SKIP_SECTION_E" = false ]; then
    process_section_e
    SECTION_E_RESULT=$?
else
    echo -e "${YELLOW}Skipping Section E processing as requested${NC}"
    SECTION_E_RESULT=0
fi

# Process Section F if not skipped
if [ "$SKIP_SECTION_F" = false ]; then
    process_section_f
    SECTION_F_RESULT=$?
else
    echo -e "${YELLOW}Skipping Section F processing as requested${NC}"
    SECTION_F_RESULT=0
fi

# Verify uploads if not skipped
if [ "$SKIP_VERIFY" = false ]; then
    verify_uploads
    VERIFY_RESULT=$?
else
    echo -e "${YELLOW}Skipping verification as requested${NC}"
    VERIFY_RESULT=0
fi

# Deactivate virtual environment if we activated it
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo -e "${BLUE}Virtual environment deactivated${NC}"
fi

# Check overall result
if [ $SECTION_E_RESULT -eq 0 ] && [ $SECTION_F_RESULT -eq 0 ] && [ $VERIFY_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}${BOLD}✓ All tasks completed successfully${NC}"
    echo -e "${BLUE}Check the log files for detailed information:${NC}"
    echo -e "  - resume_parser.log: General processing log"
    exit 0
else
    echo -e "\n${RED}${BOLD}✗ Some tasks failed${NC}"
    echo -e "${BLUE}Check the log files for error details${NC}"
    exit 1
fi 