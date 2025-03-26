const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const PROJECTS_API_URL = process.env.NEXT_PUBLIC_PROJECTS_API_URL || 'http://localhost:8001';

export interface Employee {
  id?: string;
  name: string;
  role?: string;
  email?: string;
  imageUrl?: string;
}

export interface ApiEmployee {
  id?: string;
  employee_name?: string;
  name?: string;
  role?: string;
  resume_data?: {
    Role?: string;
    [key: string]: any;
  };
  imageUrl?: string;
  score?: number;
  education?: string;
  years_experience?: number;
  relevant_projects?: any[];
  [key: string]: any;
}

export interface EmployeeDetails {
  employee_name?: string;
  name?: string;
  resume_data?: Record<string, any>;
  embedding?: any;
  file_id?: string;
  id?: string;
  role?: string;
  score?: number;
  education?: string;
  years_experience?: number;
  relevant_projects?: any[];
}

// Check if API is available
export const checkApiConnection = async (): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    console.log(`Checking API connection to: ${API_URL}/api/employees`);
    const response = await fetch(`${API_URL}/api/employees`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json'
      }
    });
    
    clearTimeout(timeoutId);
    console.log(`API connection check result: ${response.status} ${response.statusText}`);
    return response.ok;
  } catch (error) {
    console.error('API connection check failed:', error);
    return false;
  }
};

// Fetch all employees
export const getEmployees = async (): Promise<Employee[]> => {
  try {
    console.log(`Fetching employees from: ${API_URL}/api/employees`);
    
    // Use basic fetch with minimal options to avoid CORS issues
    const response = await fetch(`${API_URL}/api/employees`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error (${response.status}): ${errorText}`);
      throw new Error(`Failed to fetch employees: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('API response received:', data);
    
    // Handle the actual API response format
    const employeesArray = data.employees || data;
    
    // If no data or empty array, return empty array
    if (!employeesArray || employeesArray.length === 0) {
      console.log('No employees found');
      return [];
    }
    
    // Map API response to our Employee interface
    return employeesArray.map((emp: ApiEmployee) => ({
      id: emp.id || emp.employee_name || emp.name,
      name: emp.employee_name || emp.name || 'Unknown',
      role: emp.role || emp.resume_data?.Role || 'Employee',
      imageUrl: emp.imageUrl,
    }));
  } catch (error) {
    console.error('Error fetching employees:', error);
    throw error;
  }
};

// Fetch employee details by name
export const getEmployeeDetails = async (name: string): Promise<EmployeeDetails> => {
  try {
    console.log(`Fetching employee details for: ${name}`);
    
    // Use basic fetch with minimal options to avoid CORS issues
    const response = await fetch(`${API_URL}/api/employees/${encodeURIComponent(name)}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error (${response.status}): ${errorText}`);
      throw new Error(`Failed to fetch employee details: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Employee details received:', data);
    
    // Format the response to match our expected structure
    if (data.employee) {
      return data.employee;
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching employee details:', error);
    throw error;
  }
};

// Search employees by query
export const searchEmployees = async (query: string): Promise<Employee[]> => {
  try {
    console.log(`Searching employees with query: ${query}`);
    
    // Use basic fetch with minimal options to avoid CORS issues
    const response = await fetch(`${API_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ query }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error (${response.status}): ${errorText}`);
      throw new Error(`Failed to search employees: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Search results received:', data);
    
    // Handle the actual API response format
    const resultsArray = data.results || data;
    
    // If no data or empty array, return empty array
    if (!resultsArray || resultsArray.length === 0) {
      console.log(`No employees found matching query: "${query}"`);
      return [];
    }
    
    // Map API response to our Employee interface
    return resultsArray.map((emp: ApiEmployee) => ({
      id: emp.id || emp.employee_name || emp.name,
      name: emp.employee_name || emp.name || 'Unknown',
      role: emp.role || emp.resume_data?.Role || 'Employee',
      imageUrl: emp.imageUrl,
    }));
  } catch (error) {
    console.error('Error searching employees:', error);
    throw error;
  }
};

// RAG search using vector_search_mistral
export interface RagSearchResponse {
  answer: string;
  fullOutput?: string;
  succeeded: boolean;
  usingFallback?: boolean;
  error?: string;
  details?: string;
}

export const ragSearch = async (query: string): Promise<RagSearchResponse> => {
  try {
    console.log(`Performing RAG search with query: ${query}`);
    
    // Call the NEXT.JS local API route (not the backend server)
    const response = await fetch(`/api/rag-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ query }),
    });
    
    const data = await response.json();
    console.log('RAG search results received:', data);
    
    if (!response.ok) {
      return {
        answer: data.message || "Error executing search command. Please try again.",
        succeeded: false,
        error: data.error,
        details: data.details
      };
    }
    
    return {
      answer: data.answer || "No information found for your query.",
      fullOutput: data.fullOutput,
      succeeded: data.succeeded !== false,
      usingFallback: data.usingFallback
    };
  } catch (error) {
    console.error('Error performing RAG search:', error);
    
    return {
      answer: error instanceof Error 
        ? `Error: ${error.message}. Please try again.` 
        : "An unexpected error occurred. Please try again.",
      succeeded: false,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
};

export { API_URL, PROJECTS_API_URL }; 