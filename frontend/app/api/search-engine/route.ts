import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

interface ExecError extends Error {
  code?: number;
  signal?: string;
  cmd?: string;
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
    
    // Build the command to execute search_engine.py
    const pythonCmd = 'python';
    
    // Command to execute the search_engine.py script with the query
    const command = `cd "${rootDir}" && ${pythonCmd} backend/OLAP_QueryEngine/search_engine.py "${sanitizedQuery}"`;
    
    console.log(`Executing command: ${command}`);
    
    const { stdout, stderr } = await execPromise(command);
    
    console.log("Command executed successfully");
    console.log("STDOUT length:", stdout.length);
    
    if (stderr) {
      console.warn(`Command stderr: ${stderr}`);
    }
    
    // Clean the output if needed
    let answer = stdout.trim()
      // Remove SEARCH RESPONSE header and separator lines
      .replace(/={80,}\s*SEARCH RESPONSE\s*={80,}/g, '')
      // Remove any separator lines that are just a series of equal signs
      .replace(/^={10,}$/gm, '')
      // Clean up extra blank lines
      .replace(/\n{3,}/g, '\n\n')
      .trim();
    
    // Fix all source link formats to use standard markdown
    // This is a more comprehensive approach to catch various source formats
    answer = answer.replace(/- \*\*Source\*\*: \[(.*?)\]\((https?:\/\/[^\)]+)\)/g, (match, id, url) => {
      return `- **Source**: [${id}](${url})`;
    });
    
    // Also handle the format that doesn't use markdown style links
    answer = answer.replace(/- \*\*Source\*\*: (.*?\.pdf)\s*\((https?:\/\/[^\)]+)\)/g, (match, filename, url) => {
      return `- **Source**: [${filename}](${url})`;
    });

    // Handle the direct in-line *Source* or **Source** format 
    answer = answer.replace(/\*\*?Source\*\*?:\s*\[(.*?)\]\((https?:\/\/[^\)]+)\)/g, (match, id, url) => {
      return `**Source**: [${id}](${url})`;
    });
    
    // Handle the bare format "Source: filename.pdf (url)"
    answer = answer.replace(/\*?\*?Source\*?\*?:\s+([\w\.-]+\.pdf)\s+\((https?:\/\/[^\)]+)\)/g, (match, filename, url) => {
      return `Source: [${filename}](${url})`;
    });
    
    // Clean up asterisks in headers to avoid showing raw markdown
    // Replace **Text**: with bold styling that will be properly displayed
    answer = answer.replace(/\*\*(.*?)\*\*:/g, '$1:');
    
    // Replace *Text*: with proper styling
    answer = answer.replace(/- \*(.*?)\*:/g, '- $1:');
    
    return NextResponse.json({ 
      answer, 
      fullOutput: stdout.trim(),
      succeeded: true
    });
    
  } catch (error) {
    const execError = error as ExecError;
    console.error('Error executing search engine command:', execError);
    
    return NextResponse.json({ 
      answer: 'Sorry, there was an error processing your request. Please try again.',
      error: execError.message,
      succeeded: false
    }, { status: 500 });
  }
} 