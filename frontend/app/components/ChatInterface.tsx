'use client';

import { useState, useRef, useEffect } from 'react';
import config from '../config';
import { ragSearch, RagSearchResponse } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isUser?: boolean;
  text?: string;
  metadata?: { 
    usingFallback?: boolean;
  };
}

interface ChatInterfaceProps {
  onClose: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    // Only add welcome message if there are no messages yet
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: config.chatWelcomeMessage,
        timestamp: new Date(),
        isUser: false,
        text: config.chatWelcomeMessage
      }]);
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput('');
    
    // Add user message to chat
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
      isUser: true,
      text: userMessage
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    
    // Show loading state
    setLoading(true);
    setError(null);
    
    console.log(`Sending query to RAG search: ${userMessage}`);
    
    try {
      const response: RagSearchResponse = await ragSearch(userMessage);
      console.log('RAG response received:', response);
      
      if (!response.succeeded) {
        throw new Error(response.error || 'Failed to get a response');
      }
      
      // Format the answer for better display
      let formattedAnswer = response.answer || "I couldn't find any relevant information.";
      
      // Clean up the response text
      formattedAnswer = formattedAnswer
        .replace(/^```\s*|\s*```$/g, '') // Remove code blocks if present
        .trim();
        
      // Add system response to chat
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formattedAnswer,
        timestamp: new Date(),
        isUser: false,
        text: formattedAnswer,
        metadata: response.usingFallback ? { usingFallback: true } : undefined
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (err) {
      console.error('Error in RAG search:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      
      // Add error message to chat
      const errorMessage = err instanceof Error 
        ? `Sorry, I encountered an error: ${err.message}` 
        : 'Sorry, I encountered an error while processing your request.';
        
      const errorAssistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date(),
        isUser: false,
        text: errorMessage
      };
      
      setMessages(prev => [...prev, errorAssistantMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-20 right-5 w-80 sm:w-96 h-[500px] bg-white rounded-lg shadow-lg flex flex-col z-50 border border-gray-200">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-3 rounded-t-lg flex justify-between items-center">
        <h3 className="font-semibold">
          {config.chatTitle || "Project Assistant"}
        </h3>
        <button 
          onClick={onClose}
          className="text-white hover:text-gray-200 focus:outline-none"
        >
          <span className="sr-only">Close</span>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-2" ref={messagesEndRef}>
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`mb-4 ${message.isUser ? 'text-right' : 'text-left'}`}
          >
            <div 
              className={`inline-block p-3 rounded-lg ${
                message.isUser 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {message.isUser ? (
                message.text || message.content
              ) : (
                <div className="whitespace-pre-wrap">
                  {/* Format the assistant response with line breaks and sections */}
                  {(message.text || message.content).split('\n').map((line, i) => {
                    // Highlight section headers and results count
                    if (line.includes('Person Summary:') || line.includes('Found') && line.includes('results:')) {
                      return (
                        <div key={i} className="font-semibold text-blue-700 mb-1 mt-2">
                          {line}
                        </div>
                      );
                    }
                    // Regular line
                    return <div key={i}>{line}</div>;
                  })}
                </div>
              )}
              {message.metadata?.usingFallback && (
                <div className="text-xs mt-1 text-gray-400">
                  (Using fallback search)
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-left mb-4">
            <div className="inline-block p-3 rounded-lg bg-gray-200 text-gray-800">
              <div className="flex items-center space-x-2">
                <div className="dot-typing"></div>
                <span className="text-sm text-gray-600 ml-2">Searching documents...</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                This may take a few seconds
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="text-center text-red-500 my-2">
            {error}
          </div>
        )}
      </div>
      
      {/* Input form */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something about our projects..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white p-2 rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
          </svg>
        </button>
      </form>
      
      {/* Style for the loading animation */}
      <style jsx>{`
        .dot-typing {
          position: relative;
          left: -9999px;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background-color: #9ca3af;
          color: #9ca3af;
          box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          animation: dot-typing 1.5s infinite linear;
        }
        
        @keyframes dot-typing {
          0% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
          16.667% {
            box-shadow: 9984px -6px 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
          33.333% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
          50% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px -6px 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
          66.667% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
          83.333% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px -6px 0 0 #9ca3af;
          }
          100% {
            box-shadow: 9984px 0 0 0 #9ca3af, 9999px 0 0 0 #9ca3af, 10014px 0 0 0 #9ca3af;
          }
        }
      `}</style>
    </div>
  );
};

export default ChatInterface; 