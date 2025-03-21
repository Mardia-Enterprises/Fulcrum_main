'use client';

import { useState, useRef, useEffect } from 'react';
import config from '../config';
import { ragSearch, RagSearchResponse } from '../services/api';
import Link from 'next/link';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isUser?: boolean;
  text?: string;
  metadata?: { 
    usingFallback?: boolean;
    fileReferences?: string[];
  };
}

interface ChatSession {
  id: string;
  title: string;
  lastUpdated: Date;
  messages: Message[];
}

interface FullPageChatProps {
  onClose: () => void;
}

const FullPageChat: React.FC<FullPageChatProps> = ({ onClose }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat sessions from localStorage
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      try {
        // Parse the date objects which are stored as strings
        const parsedSessions = JSON.parse(savedSessions, (key, value) => {
          if (key === 'timestamp' || key === 'lastUpdated') {
            return new Date(value);
          }
          return value;
        });
        setSessions(parsedSessions);
        
        // If there are sessions, set the current session to the most recent one
        if (parsedSessions.length > 0) {
          const mostRecentSession = parsedSessions.sort(
            (a: ChatSession, b: ChatSession) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime()
          )[0];
          setCurrentSessionId(mostRecentSession.id);
          setMessages(mostRecentSession.messages);
        } else {
          // If no sessions, create a new one
          createNewSession();
        }
      } catch (err) {
        console.error('Error parsing saved sessions:', err);
        createNewSession();
      }
    } else {
      // If no sessions, create a new one
      createNewSession();
    }
  }, []);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('chatSessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  // Initialize with welcome message
  useEffect(() => {
    // Only add welcome message if there are no messages yet
    if (messages.length === 0 && currentSessionId) {
      const welcomeMessage: Message = {
        id: 'welcome',
        role: 'assistant',
        content: config.chatWelcomeMessage,
        timestamp: new Date(),
        isUser: false,
        text: config.chatWelcomeMessage
      };
      
      setMessages([welcomeMessage]);
      
      // Update the session with the welcome message
      updateSessionMessages(currentSessionId, [welcomeMessage]);
    }
  }, [currentSessionId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Create a new chat session
  const createNewSession = () => {
    const newSessionId = Date.now().toString();
    const newSession: ChatSession = {
      id: newSessionId,
      title: 'New Conversation',
      lastUpdated: new Date(),
      messages: []
    };
    
    setSessions(prev => [...prev, newSession]);
    setCurrentSessionId(newSessionId);
    setMessages([]);
    
    return newSessionId;
  };

  // Update session messages
  const updateSessionMessages = (sessionId: string, newMessages: Message[]) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        // Update the title based on the first user message if it exists
        const firstUserMessage = newMessages.find(msg => msg.role === 'user');
        const title = firstUserMessage 
          ? firstUserMessage.content.substring(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '')
          : 'New Conversation';
          
        return {
          ...session,
          title,
          lastUpdated: new Date(),
          messages: newMessages
        };
      }
      return session;
    }));
  };

  // Switch to a different session
  const switchSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setMessages(session.messages);
      setInput('');
      setError(null);
    }
  };

  // Delete a session
  const deleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering switchSession
    
    setSessions(prev => prev.filter(session => session.id !== sessionId));
    
    // If we're deleting the current session, switch to another one or create a new one
    if (sessionId === currentSessionId) {
      const remainingSessions = sessions.filter(session => session.id !== sessionId);
      if (remainingSessions.length > 0) {
        const newCurrentSession = remainingSessions[0];
        setCurrentSessionId(newCurrentSession.id);
        setMessages(newCurrentSession.messages);
      } else {
        createNewSession();
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || !currentSessionId) return;
    
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
    
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);
    updateSessionMessages(currentSessionId, updatedMessages);
    
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
      let fileReferences: string[] = [];
      
      // Extract file references from raw output if available
      if (response.fullOutput) {
        // First try to extract filenames from "File:" lines
        const fileLines = response.fullOutput.match(/File: ([^:\n]+\.pdf)/g);
        if (fileLines) {
          fileReferences = fileLines.map(line => {
            return line.replace(/File: /, '').trim();
          });
        }
        
        // Then try to extract from "Result X (Score: Y)" format
        if (fileReferences.length === 0) {
          const resultLines = response.fullOutput.split('\n');
          for (let i = 0; i < resultLines.length; i++) {
            const line = resultLines[i];
            if (line.match(/^Result \d+ \(Score: [\d.]+\)$/i) && i + 1 < resultLines.length) {
              const nextLine = resultLines[i + 1].trim();
              if (nextLine && nextLine.endsWith('.pdf')) {
                fileReferences.push(nextLine);
              }
            }
          }
        }
        
        // Remove duplicates
        fileReferences = Array.from(new Set(fileReferences));
      }
      
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
        metadata: {
          usingFallback: response.usingFallback ? true : false,
          fileReferences: fileReferences
        }
      };
      
      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      updateSessionMessages(currentSessionId, finalMessages);
      
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
      
      const finalMessages = [...updatedMessages, errorAssistantMessage];
      setMessages(finalMessages);
      updateSessionMessages(currentSessionId, finalMessages);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === now.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="h-screen flex flex-col lg:pl-72">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-3 flex justify-between items-center shadow-md">
        <div className="flex items-center">
          {/* Mobile sidebar toggle */}
          <button 
            className="md:hidden mr-3 text-white"
            onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </button>
          
          <h1 className="text-xl font-semibold">
            {config.chatTitle || "Project Assistant"}
          </h1>
        </div>
        <button 
          onClick={onClose}
          className="text-white hover:text-gray-200 focus:outline-none py-2 px-4 rounded-md border border-blue-500 hover:bg-blue-700 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
      
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat Sidebar */}
        <div className={`
          bg-gray-800 text-white w-64 flex-shrink-0 flex flex-col
          md:block 
          ${isMobileSidebarOpen ? 'absolute inset-y-0 left-0 z-50 mt-14 h-[calc(100%-3.5rem)]' : 'hidden'}
        `}>
          {/* New Chat Button */}
          <div className="p-4 border-b border-gray-700">
            <button 
              onClick={() => {
                const newId = createNewSession();
                switchSession(newId);
                if (isMobileSidebarOpen) setIsMobileSidebarOpen(false);
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md flex items-center justify-center transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              New Chat
            </button>
          </div>
          
          {/* Chat List */}
          <div className="flex-1 overflow-y-auto">
            {sessions.length > 0 ? (
              sessions
                .sort((a: ChatSession, b: ChatSession) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime())
                .map(session => (
                  <div 
                    key={session.id}
                    onClick={() => {
                      switchSession(session.id);
                      if (isMobileSidebarOpen) setIsMobileSidebarOpen(false);
                    }}
                    className={`
                      p-3 border-b border-gray-700 cursor-pointer flex justify-between items-start
                      hover:bg-gray-700 transition-colors
                      ${currentSessionId === session.id ? 'bg-gray-700' : ''}
                    `}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{session.title}</div>
                      <div className="text-xs text-gray-400">{formatDate(new Date(session.lastUpdated))}</div>
                    </div>
                    
                    <button 
                      onClick={(e) => deleteSession(session.id, e)}
                      className="ml-2 text-gray-400 hover:text-red-400"
                      aria-label="Delete conversation"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </button>
                  </div>
                ))
            ) : (
              <div className="p-4 text-gray-400 text-center">No conversations yet</div>
            )}
          </div>
        </div>
        
        {/* Chat Area */}
        <div className="flex-1 flex flex-col max-h-full">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50" ref={messagesEndRef}>
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`mb-6 ${message.isUser ? 'text-right' : 'text-left'}`}
              >
                <div 
                  className={`inline-block p-4 rounded-lg max-w-[85%] ${
                    message.isUser 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-gray-800 border border-gray-200 shadow-sm'
                  }`}
                >
                  {message.isUser ? (
                    message.text || message.content
                  ) : (
                    <div className="whitespace-pre-wrap">
                      {(() => {
                        const content = message.text || message.content;
                        const lines = content.split('\n');
                        const fileReferences = message.metadata?.fileReferences || [];
                        
                        // Find where enhanced results start
                        const enhancedIndex = lines.findIndex(line => 
                          line.includes('Enhanced Results:') ||
                          line.match(/^Summary on .*:$/) || 
                          (line.includes('Project Description:') && !line.includes('DESCRIPTION'))
                        );
                        
                        // Find where raw search results start
                        const rawSearchIndex = lines.findIndex(line => 
                          line.includes('Raw Search Results:') || 
                          line.includes('Found') && line.includes('results:')
                        );
                        
                        // If we have enhanced results or file references
                        if (enhancedIndex !== -1 || fileReferences.length > 0) {
                          let enhancedResults = [];
                          let referenceLinks = [];
                          
                          // Process enhanced results first (if present)
                          if (enhancedIndex !== -1) {
                            let i = enhancedIndex;
                            
                            // If the line is "Enhanced Results:", skip it
                            if (lines[i].includes('Enhanced Results:')) {
                              i++;
                            }
                            
                            // Process each line until we hit raw search results or the end
                            while (i < lines.length) {
                              const line = lines[i];
                              
                              // If we hit raw search results, stop processing enhanced results
                              if (line.includes('Raw Search Results:') || 
                                  (line.match(/^Result \d+ \(Score: [\d.]+\)$/) && i < lines.length - 1 && lines[i+1].endsWith('.pdf'))) {
                                break;
                              }
                              
                              // Section heading
                              if (line.match(/^Summary on .*:$/) || line.match(/^\d+\.\s+.*:$/) && !line.includes('Result')) {
                                enhancedResults.push(
                                  <div key={`enhanced-${i}`} className="font-semibold text-blue-700 mb-2 mt-2">
                                    {line}
                                  </div>
                                );
                              }
                              // Numbered section (project details, etc)
                              else if (line.match(/^\d+\.\s+.*:$/)) {
                                enhancedResults.push(
                                  <div key={`enhanced-${i}`} className="font-semibold mt-3 mb-1">
                                    {line}
                                  </div>
                                );
                              }
                              // Bullet point
                              else if (line.trim().startsWith('-')) {
                                enhancedResults.push(
                                  <div key={`enhanced-${i}`} className="ml-4 mb-1">
                                    {line}
                                  </div>
                                );
                              }
                              // Regular line (if not empty or a header)
                              else if (line.trim() && 
                                      !line.includes('Enhanced Results:') && 
                                      !line.includes('Raw Search Results:')) {
                                enhancedResults.push(
                                  <div key={`enhanced-${i}`} className="mb-1">
                                    {line}
                                  </div>
                                );
                              }
                              
                              i++;
                            }
                          }
                          
                          // Add reference links from file references
                          if (fileReferences.length > 0) {
                            // Add the "References:" heading
                            referenceLinks.push(
                              <div key="ref-heading" className="font-semibold mt-4 mb-2">
                                References:
                              </div>
                            );
                            
                            // Add each file reference as a link to try all three buckets
                            fileReferences.forEach((fileName, index) => {
                              // Create separate links for each bucket
                              const buckets = ["pdf-docs", "section-e-resumes", "section-f-resumes"];
                              
                              referenceLinks.push(
                                <div key={`ref-${index}`} className="ml-4 text-blue-600 hover:underline mb-2">
                                  {buckets.map((bucket, bucketIndex) => (
                                    <a 
                                      key={`${bucket}-${index}`}
                                      href={`https://khqwfkvnwtovvcbidwnl.supabase.co/storage/v1/object/public/${bucket}/${encodeURIComponent(fileName)}`}
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className={bucketIndex > 0 ? "ml-3" : ""}
                                      onClick={(e) => {
                                        // Prevent default to handle click manually
                                        e.preventDefault();
                                        // Open the link in a new tab
                                        window.open(`https://khqwfkvnwtovvcbidwnl.supabase.co/storage/v1/object/public/${bucket}/${encodeURIComponent(fileName)}`, '_blank');
                                      }}
                                    >
                                      {bucketIndex === 0 ? fileName : `[${bucket.split('-')[0]}]`}
                                    </a>
                                  ))}
                                </div>
                              );
                            });
                          }
                          
                          // Return the combined elements
                          return [...enhancedResults, ...referenceLinks];
                        } else {
                          // Default formatting for other types of responses
                          return lines.map((line, i) => (
                            <div key={i} className="mb-1">{line}</div>
                          ));
                        }
                      })()}
                    </div>
                  )}
                  {message.metadata?.usingFallback && (
                    <div className="text-xs mt-2 text-gray-500">
                      (Using fallback search)
                    </div>
                  )}
                  <div className="text-xs mt-2 text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-left mb-4">
                <div className="inline-block p-4 rounded-lg bg-white text-gray-800 border border-gray-200 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="dot-typing"></div>
                    <span className="text-sm text-gray-600 ml-2">Searching documents...</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    This may take a few seconds
                  </div>
                </div>
              </div>
            )}
            {error && (
              <div className="text-center text-red-500 my-4 p-3 bg-red-50 rounded-lg border border-red-200">
                {error}
              </div>
            )}
          </div>
          
          {/* Input form */}
          <div className="border-t border-gray-200 bg-white p-4">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask something about our projects or employees..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
      
      {/* Style for the loading animation */}
      <style jsx>{`
        .dot-typing {
          position: relative;
          left: -9999px;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: #6b7280;
          color: #6b7280;
          box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          animation: dot-typing 1.5s infinite linear;
        }
        
        @keyframes dot-typing {
          0% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
          16.667% {
            box-shadow: 9984px -10px 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
          33.333% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
          50% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px -10px 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
          66.667% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
          83.333% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px -10px 0 0 #6b7280;
          }
          100% {
            box-shadow: 9984px 0 0 0 #6b7280, 9999px 0 0 0 #6b7280, 10014px 0 0 0 #6b7280;
          }
        }
      `}</style>
    </div>
  );
};

export default FullPageChat;