// Environment variables and configuration settings
const config = {
  // API URLs
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Chat settings
  chatTitle: 'Database Assistant',
  chatWelcomeMessage: 'Hello! I can help you find information about teams, projects, and their relationships in our database. Ask me questions like "Who is working on the airport project?" or "What projects are our civil engineers working on?"',
  
  // Paths to Python modules
  pythonModulePath: 'backend.OLAP_QueryEngine.search_engine',
  
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