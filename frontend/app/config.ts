// Environment variables and configuration settings
const config = {
  // API URLs
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Chat settings
  chatTitle: 'Project Assistant',
  chatWelcomeMessage: 'Hello! How can I help you with information about our projects and team?',
  
  // Paths to Python modules
  pythonModulePath: 'backend.vector_search_mistral.run',
  
  // RAG search settings
  ragSearch: {
    // Command execution options
    pythonCommand: 'python',  // or 'python3' on some systems
    fallbackPythonCommand: 'python3',
    useRagFlag: true,
    topK: 5,
    alpha: 0.5,
    
    // Result formatting
    highlightPersonSummary: true,
    extractSummarySection: true,
    
    // Error handling
    retryOnFailure: true,
    maxRetries: 1,
  },
  
  // Application settings  
  appName: 'Fulcrum - Team Directory',
};

export default config; 