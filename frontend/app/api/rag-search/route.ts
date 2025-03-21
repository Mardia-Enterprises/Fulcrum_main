import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import config from '../../config';

const execPromise = promisify(exec);

interface ExecError extends Error {
  code?: number;
  signal?: string;
  cmd?: string;
}

// Function to format command output consistently
function formatCommandOutput(stdout: string): string {
  let answer = stdout.trim();
  
  // Process the output based on config settings
  if (config.ragSearch.extractSummarySection) {
    // Check if the output contains "Found X results" pattern
    const resultsFoundMatch = stdout.match(/Found (\d+) results/i);
    if (resultsFoundMatch) {
      const numResults = resultsFoundMatch[1];
      
      // Extract the actual search results that typically follow the "Found X results" line
      // This regex looks for content after "Found X results" up to the end or before "Person Summary:" if it exists
      const resultsSection = stdout.match(/Found \d+ results.*?\n([\s\S]+?)(?=Person Summary:|$)/i);
      
      if (resultsSection && resultsSection[1]) {
        // Format the results section nicely
        const formattedResults = resultsSection[1].trim()
          .split(/\n{2,}/)  // Split by double newlines to get individual results
          .map(result => result.trim())
          .filter(result => result.length > 0)
          .map(result => {
            // Format each result - remove excess whitespace and add proper line breaks
            return result.replace(/\n\s+/g, '\n').trim();
          })
          .join('\n\n');
          
        answer = `Found ${numResults} results:\n\n${formattedResults}`;
      }
    }
    
    // Look for person summaries which have a specific format
    const personSummaryMatch = stdout.match(/Person Summary:([\s\S]+?)(?=\n\n\n|$)/);
    if (personSummaryMatch && personSummaryMatch[1]) {
      // Format the person summary - this is often the most valuable part of the output
      const formattedSummary = personSummaryMatch[1].trim()
        .replace(/\n\s+/g, '\n')  // Remove excessive indentation
        .replace(/\n{3,}/g, '\n\n');  // Replace triple+ newlines with double
        
      // If we have both results and a person summary, combine them
      if (answer.includes('Found') && answer.includes('results')) {
        answer = `${answer}\n\n**Person Summary:**${formattedSummary}`;
      } else {
        answer = `**Person Summary:**${formattedSummary}`;
      }
    }
    
    // If no specific sections were found, look for an explicit answer section
    if (!answer.includes('Person Summary') && !answer.includes('Found') && !answer.includes('results')) {
      const answerMatch = stdout.match(/(?:Answer:|AI Response:)([\s\S]+?)(?=\n\n\n|$)/i);
      if (answerMatch && answerMatch[1]) {
        answer = answerMatch[1].trim();
      } else if (stdout.length > 0) {
        // If no structured output is found, use the entire output but clean it up
        answer = stdout.trim()
          .replace(/\n{3,}/g, '\n\n')  // Replace excessive newlines
          .replace(/\n\s+/g, '\n');    // Remove excessive indentation
          
        // If the output is very long, extract a reasonable portion
        if (answer.length > 1500) {
          answer = answer.substring(0, 1500) + "...\n\n(Response truncated due to length)";
        }
      }
    }
  }
  
  // Clean up the response
  answer = answer.replace(/^\s*```\s*|\s*```\s*$/g, ''); // Remove code blocks
  
  // Convert simple markdown to HTML-friendly format
  answer = answer
    .replace(/\*\*(.*?)\*\*/g, '$1') // Make bold text normal (we'll style it with CSS)
    .replace(/\n/g, '\n'); // Preserve line breaks
    
  return answer;
}

export async function POST(request: NextRequest) {
  try {
    const data = await request.json();
    const { query } = data;
    
    if (!query) {
      return NextResponse.json(
        { error: 'Query parameter is required' },
        { status: 400 }
      );
    }

    // Sanitize the query to prevent command injection
    const sanitizedQuery = query.replace(/[;"'|&$<>]/g, '');
    
    // Get the correct root directory for the project
    const rootDir = process.env.ROOT_DIR || path.resolve(process.cwd(), '../');
    
    // Log the directories for debugging
    console.log('Current directory:', process.cwd());
    console.log('Root directory:', rootDir);
    
    // Build the command with parameters from config
    const ragFlag = config.ragSearch.useRagFlag ? ' --rag' : '';
    const topK = config.ragSearch.topK ? ` --top-k ${config.ragSearch.topK}` : '';
    const alpha = config.ragSearch.alpha !== undefined ? ` --alpha ${config.ragSearch.alpha}` : '';
    
    // Build the full command with virtual environment activation and absolute paths
    const pythonCmd = config.ragSearch.pythonCommand;
    const activateVenvCmd = process.platform === 'win32' 
      ? 'call venv\\Scripts\\activate' 
      : 'source venv/bin/activate';
    
    // Check if .env file exists and add export command if needed
    const dotEnvPath = path.join(rootDir, '.env');
    const exportEnvCmd = `if [ -f "${dotEnvPath}" ]; then export $(grep -v '^#' "${dotEnvPath}" | xargs -0); echo "Using .env file"; fi`;
    
    // Try different command structures to find one that works
    // Option 1: Use the backend/ directory path directly with vector_search_mistral.run
    const command1 = `cd "${rootDir}" && ${exportEnvCmd} && ${activateVenvCmd} && cd backend && ${pythonCmd} -m vector_search_mistral.run search "${sanitizedQuery}"${ragFlag}${topK}${alpha}`;
    
    // Option 2: Use the command directly from the root directory
    const command2 = `cd "${rootDir}" && ${exportEnvCmd} && ${activateVenvCmd} && ${pythonCmd} -m backend.vector_search_mistral.run search "${sanitizedQuery}"${ragFlag}${topK}${alpha}`;
    
    // Option 3: Use the Python path directly without module notation
    const command3 = `cd "${rootDir}" && ${exportEnvCmd} && ${activateVenvCmd} && ${pythonCmd} backend/vector_search_mistral/run.py search "${sanitizedQuery}"${ragFlag}${topK}${alpha}`;
    
    // Start with the first command approach
    const command = command1;
    
    console.log(`Executing command: ${command}`);
    
    try {
      const { stdout, stderr } = await execPromise(command);
      
      console.log("Command executed successfully");
      console.log("STDOUT length:", stdout.length);
      
      if (stderr) {
        console.warn(`Command stderr: ${stderr}`);
      }
      
      // Use the formatting function
      const answer = formatCommandOutput(stdout);
      
      return NextResponse.json({ 
        answer, 
        fullOutput: stdout.trim(),
        succeeded: true,
        approach: 1
      });
    } catch (error) {
      const execError = error as ExecError;
      console.error('Error executing command approach 1:', execError);
      
      // Try the second command approach if the first fails
      try {
        console.log(`Trying second command approach: ${command2}`);
        const { stdout, stderr } = await execPromise(command2);
        
        console.log("Second command approach executed successfully");
        console.log("STDOUT length:", stdout.length);
        
        if (stderr) {
          console.warn(`Command stderr: ${stderr}`);
        }
        
        // Use the formatting function here too
        const answer = formatCommandOutput(stdout);
        
        return NextResponse.json({ 
          answer, 
          fullOutput: stdout.trim(),
          succeeded: true,
          approach: 2
        });
      } catch (secondError) {
        console.error('Error executing command approach 2:', secondError);
        
        // Try the third command approach if the second fails
        try {
          console.log(`Trying third command approach: ${command3}`);
          const { stdout, stderr } = await execPromise(command3);
          
          console.log("Third command approach executed successfully");
          
          // Use the formatting function here too
          const answer = formatCommandOutput(stdout);
          
          return NextResponse.json({ 
            answer, 
            fullOutput: stdout.trim(),
            succeeded: true,
            approach: 3
          });
        } catch (thirdError) {
          console.error('Error executing command approach 3:', thirdError);
          
          // If retry is enabled and this is a command not found error, try an alternative approach
          const error3 = thirdError as ExecError;
          if (config.ragSearch.retryOnFailure && 
              (error3.message?.includes('not found') || error3.message?.includes('No such file'))) {
            console.log('Trying alternative command execution...');
            
            // Try with the fallback Python command
            const fallbackPythonCmd = config.ragSearch.fallbackPythonCommand;
            const altCommand = `cd "${rootDir}" && ${exportEnvCmd} && ${activateVenvCmd} && cd backend && ${fallbackPythonCmd} -m vector_search_mistral.run search "${sanitizedQuery}"${ragFlag}${topK}${alpha}`;
            
            console.log(`Executing alternative command: ${altCommand}`);
            
            try {
              const { stdout, stderr } = await execPromise(altCommand);
              console.log("Alternative command executed successfully");
              
              // Format the output with our consistent formatter
              const answer = formatCommandOutput(stdout);
              
              return NextResponse.json({ 
                answer,
                fullOutput: stdout.trim(),
                succeeded: true,
                usingFallback: true
              });
            } catch (error) {
              const altError = error as ExecError;
              console.error('Alternative command also failed:', altError);
              
              // Last resort: Try a simple Python test to see if we can run Python at all
              try {
                console.log('Trying basic Python test command');
                const basicCommand = `cd "${rootDir}" && ${fallbackPythonCmd} -c "import sys; print('Python is working. Version:', sys.version); print('Available modules:', sys.modules.keys())"`;
                const { stdout: basicOutput } = await execPromise(basicCommand);
                
                return NextResponse.json({ 
                  answer: `Failed to run vector search. Python is available but there was a problem running the module.\n\nPython info: ${basicOutput.trim()}`,
                  error: altError.message,
                  succeeded: false,
                  details: 'Module execution failed, but Python is available.'
                });
              } catch (finalError) {
                console.error('Basic Python test also failed:', finalError);
                throw new Error(`Cannot run any Python commands. There may be a fundamental issue with the Python installation or environment.`);
              }
            }
          }
          
          throw new Error(`Command execution failed: ${error3.message || 'Unknown error'}`);
        }
      }
      
      throw new Error(`Command execution failed: ${execError.message}`);
    }
  } catch (error) {
    console.error('Error processing RAG search:', error);
    return NextResponse.json(
      { 
        error: 'Failed to process search request', 
        details: error instanceof Error ? error.message : String(error),
        message: "The server encountered an error processing your request. Please ensure the backend Python environment is correctly set up and the vector_search_mistral module is accessible.",
        succeeded: false
      },
      { status: 500 }
    );
  }
} 