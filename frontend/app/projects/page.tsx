'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ErrorBoundary from '../components/ErrorBoundary'
import { PROJECTS_API_URL } from '../services/api';

interface Project {
  id?: string;
  title: string;
  brief_description?: string;
  project_owner?: string;
  location?: string;
  project_type?: string | string[];
  category?: string | string[];
  year_completed?: any;
  project_cost?: string | number;
  construction_cost?: string | number;
  [key: string]: any; // Allow for additional fields
}

// Helper to get the Projects API URL (port 8001)
const getProjectsApiUrl = () => {
  return PROJECTS_API_URL;
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [projectToDelete, setProjectToDelete] = useState<string>('')
  const [showFileUpload, setShowFileUpload] = useState(false)
  const [showDeleteInput, setShowDeleteInput] = useState(false)
  const [showMergeForm, setShowMergeForm] = useState(false)
  const [sourceProject, setSourceProject] = useState<string>('')
  const [targetProject, setTargetProject] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [projectTitle, setProjectTitle] = useState<string>('')

  useEffect(() => {
    fetchProjects()
  }, [])

  async function fetchProjects() {
    try {
      setLoading(true)
      // Use port 8001 for the Projects API
      const projectsApiUrl = getProjectsApiUrl()
      console.log('Fetching projects from:', `${projectsApiUrl}/api/projects`)
      
      const response = await fetch(`${projectsApiUrl}/api/projects`, {
        headers: { 'Accept': 'application/json' }
      })
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('API response:', data)
      
      // Extract projects from the response
      const projectsList = data.projects || data
      
      if (Array.isArray(projectsList) && projectsList.length > 0) {
        const mapped = projectsList.map((proj: any) => {
          // Better handling for title_and_location
          let title = 'Unknown Project';
          try {
            // Try to extract the title with better validation
            if (typeof proj.title_and_location === 'string') {
              title = proj.title_and_location;
            } else if (proj.project_key && typeof proj.project_key === 'string') {
              title = proj.project_key;
            } else if (proj.id && typeof proj.id === 'string') {
              title = `Project ${proj.id}`;
            }
          } catch (error) {
            console.error('Error processing project title:', error);
          }

          // Create a project object with all valid fields
          const project: Project = {
            id: proj.id || `project-${Math.random().toString(36).substr(2, 9)}`,
            title: title,
            brief_description: proj.brief_description || 'No description available',
            project_owner: proj.project_owner || 'Unknown'
          };

          // Copy additional fields if they exist
          if (proj.location) project.location = proj.location;
          if (proj.project_type) project.project_type = proj.project_type;
          if (proj.category) project.category = proj.category;
          if (proj.year_completed) project.year_completed = proj.year_completed;
          if (proj.project_cost) project.project_cost = proj.project_cost;
          if (proj.construction_cost) project.construction_cost = proj.construction_cost;
          
          // Copy any other primitive fields
          Object.keys(proj).forEach(key => {
            if (!project[key] && 
                (typeof proj[key] === 'string' || 
                 typeof proj[key] === 'number' || 
                 typeof proj[key] === 'boolean')) {
              project[key] = proj[key];
            }
          });
          
          return project;
        });
        
        setProjects(mapped)
        setError(null)
      } else {
        // Fallback to sample data if API returns empty array
        setError('No projects found')
      }
    } catch (err: any) {
      console.error('Error fetching projects:', err)
      
      // Provide more specific error messages
      if (err.message.includes('Failed to fetch') || err.message.includes('Network error')) {
        setError(`Projects API is not running. Please make sure the backend Projects API is running on port 8001.`)
      } else if (err.message.includes('404')) {
        setError(`Projects API endpoint not found. Make sure the API server is running on the correct path.`)
      } else {
        setError(`Failed to load projects: ${err.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const uploadProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return
    
    try {
      setActionMessage(null)
      const projectsApiUrl = getProjectsApiUrl()
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (projectTitle) {
        formData.append('project_title', projectTitle)
      }
      
      const response = await fetch(`${projectsApiUrl}/api/projects`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`)
      
      const result = await response.json()
      setActionMessage({type: 'success', text: 'Project added successfully'})
      setSelectedFile(null)
      setProjectTitle('')
      setShowFileUpload(false)
      fetchProjects() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error adding project: ${err.message}`})
    }
  }

  const deleteProject = async (projectTitle: string) => {
    if (!projectTitle) return
    
    try {
      setActionMessage(null)
      const projectsApiUrl = getProjectsApiUrl()
      
      const response = await fetch(`${projectsApiUrl}/api/projects/${encodeURIComponent(projectTitle)}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) throw new Error(`Delete failed: ${response.status}`)
      
      setActionMessage({type: 'success', text: 'Project deleted successfully'})
      setProjectToDelete('')
      fetchProjects() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error deleting project: ${err.message}`})
    }
  }

  const handleProjectCardClick = (project: Project) => {
    // Navigate to the project detail page
    router.push(`/projects/${encodeURIComponent(project.title)}`);
  };

  const mergeProjects = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceProject || !targetProject) return
    
    try {
      setActionMessage(null)
      const projectsApiUrl = getProjectsApiUrl()
      
      const response = await fetch(`${projectsApiUrl}/api/merge_projects?source_title=${encodeURIComponent(sourceProject)}&target_title=${encodeURIComponent(targetProject)}`, {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error(`Merge failed: ${response.status}`)
      
      const result = await response.json()
      setActionMessage({type: 'success', text: 'Projects merged successfully'})
      setSourceProject('')
      setTargetProject('')
      setShowMergeForm(false)
      fetchProjects() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error merging projects: ${err.message}`})
    }
  }

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    try {
      setActionMessage(null)
      setLoading(true)
      const projectsApiUrl = getProjectsApiUrl()
      
      const response = await fetch(`${projectsApiUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery
        }),
      })
      
      if (!response.ok) throw new Error(`Search failed: ${response.status}`)
      
      const data = await response.json()
      console.log('Search results:', data)
      
      // Extract projects from the response
      const projectsList = data.projects || data.results || data
      
      if (Array.isArray(projectsList) && projectsList.length > 0) {
        const mapped = projectsList.map((proj: any) => {
          // Better handling for title_and_location
          let title = 'Unknown Project';
          try {
            // Try to extract the title with better validation
            if (typeof proj.title_and_location === 'string') {
              title = proj.title_and_location;
            } else if (proj.project_key && typeof proj.project_key === 'string') {
              title = proj.project_key;
            } else if (proj.id && typeof proj.id === 'string') {
              title = `Project ${proj.id}`;
            }
          } catch (error) {
            console.error('Error processing project title:', error);
          }

          // Create a project object with all valid fields
          const project: Project = {
            id: proj.id || `project-${Math.random().toString(36).substr(2, 9)}`,
            title: title,
            brief_description: proj.brief_description || 'No description available',
            project_owner: proj.project_owner || 'Unknown'
          };

          // Copy additional fields if they exist
          if (proj.location) project.location = proj.location;
          if (proj.project_type) project.project_type = proj.project_type;
          if (proj.category) project.category = proj.category;
          if (proj.year_completed) project.year_completed = proj.year_completed;
          if (proj.project_cost) project.project_cost = proj.project_cost;
          if (proj.construction_cost) project.construction_cost = proj.construction_cost;
          
          // Copy any other primitive fields
          Object.keys(proj).forEach(key => {
            if (!project[key] && 
                (typeof proj[key] === 'string' || 
                 typeof proj[key] === 'number' || 
                 typeof proj[key] === 'boolean')) {
              project[key] = proj[key];
            }
          });
          
          return project;
        });
        
        setProjects(mapped)
        setActionMessage({type: 'success', text: `Found ${mapped.length} projects matching your query`})
        setError(null)
      } else {
        setProjects([])
        setActionMessage({type: 'error', text: 'No projects found matching your query'})
      }
    } catch (err: any) {
      console.error('Error searching projects:', err)
      
      if (err.message.includes('Failed to fetch') || err.message.includes('Network error')) {
        setActionMessage({type: 'error', text: 'Projects API is not running. Please make sure the backend API is running on port 8001.'})
      } else if (err.message.includes('validation error')) {
        setActionMessage({type: 'error', text: 'Data validation error. Search results may contain invalid data.'})
      } else {
        setActionMessage({type: 'error', text: `Search failed: ${err.message}`})
      }
    } finally {
      setLoading(false)
    }
  }

  const resetSearch = () => {
    setSearchQuery('')
    fetchProjects()
  }

  return (
    <ErrorBoundary>
      <main className="py-10 lg:pl-72">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col space-y-6 mb-8">
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowFileUpload(!showFileUpload)
                  setShowDeleteInput(false)
                  setShowMergeForm(false)
                }}
                className="rounded-sm bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                Add Project
              </button>
              
              <button
                type="button"
                onClick={() => {
                  setShowMergeForm(!showMergeForm)
                  setShowFileUpload(false)
                  setShowDeleteInput(false)
                }}
                className="rounded-md bg-amber-600 px-2.5 py-1.5 text-sm font-semibold text-white shadow-xs hover:bg-amber-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600"
              >
                Merge Projects
              </button>
            </div>
            
            {showFileUpload && (
              <form onSubmit={uploadProject} className="bg-white p-4 rounded-md shadow">
                <div className="mb-4">
                  <label htmlFor="project-title" className="block text-sm font-medium text-gray-700">
                    Project Title (optional)
                  </label>
                  <input
                    id="project-title"
                    name="project_title"
                    type="text"
                    value={projectTitle}
                    onChange={(e) => setProjectTitle(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="If not provided, filename will be used"
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700">
                    Upload Project (PDF)
                  </label>
                  <input
                    id="file-upload"
                    name="file"
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={!selectedFile}
                    className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                  >
                    Upload
                  </button>
                </div>
              </form>
            )}
            
            {showMergeForm && (
              <form onSubmit={mergeProjects} className="bg-white p-4 rounded-md shadow">
                <div className="mb-4">
                  <label htmlFor="source-project" className="block text-sm font-medium text-gray-700">
                    Source Project Title (will be merged from)
                  </label>
                  <input
                    id="source-project"
                    name="source-project"
                    type="text"
                    value={sourceProject}
                    onChange={(e) => setSourceProject(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Enter exact project title"
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="target-project" className="block text-sm font-medium text-gray-700">
                    Target Project Title (will be merged into)
                  </label>
                  <input
                    id="target-project"
                    name="target-project"
                    type="text"
                    value={targetProject}
                    onChange={(e) => setTargetProject(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Enter exact project title"
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={!sourceProject || !targetProject}
                    className="rounded-md bg-amber-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-amber-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 disabled:opacity-50"
                  >
                    Merge
                  </button>
                </div>
              </form>
            )}
            
            {actionMessage && (
              <div className={`p-4 rounded-md ${actionMessage.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                {actionMessage.text}
              </div>
            )}
            
            {/* Search bar */}
            <div className="mt-6">
              <form onSubmit={handleSearchSubmit} className="flex space-x-2">
                <div className="flex-1">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search projects by location, description, owner..."
                    className="block w-full rounded-md border-0 py-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={!searchQuery.trim()}
                    className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                  >
                    Search
                  </button>
                  {projects.length > 0 && searchQuery && (
                    <button
                      type="button"
                      onClick={resetSearch}
                      className="rounded-md bg-gray-200 px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm hover:bg-gray-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-300"
                    >
                      Reset
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
          
          <h1 className="text-2xl font-bold mb-6">Projects</h1>

          {loading ? (
            <div className="bg-white shadow-md rounded-lg p-8 text-center">
              <p className="text-gray-600">Loading projects...</p>
            </div>
          ) : error ? (
            <div className="bg-white shadow-md rounded-lg p-8 text-center">
              <p className="text-red-500">{error}</p>
              {error.includes('API is not running') && (
                <div className="mt-4 p-4 bg-blue-50 text-blue-700 rounded-md text-left">
                  <h3 className="font-medium mb-2">Instructions to start the Projects API:</h3>
                  <ol className="list-decimal list-inside space-y-2">
                    <li>Navigate to the backend directory in your terminal</li>
                    <li>Activate your virtual environment (if using one)</li>
                    <li>Run <code className="bg-blue-100 px-2 py-1 rounded">cd API_projects</code></li>
                    <li>Run <code className="bg-blue-100 px-2 py-1 rounded">python run_api.py</code></li>
                  </ol>
                </div>
              )}
              <button
                onClick={() => fetchProjects()}
                className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <div 
                  key={project.id || project.title} 
                  className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer relative"
                >
                  <div 
                    className="absolute top-3 right-3 text-red-600 hover:text-red-800 z-10"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent card click
                      const confirmed = window.confirm(`Are you sure you want to delete ${project.title}?`);
                      if (confirmed) {
                        deleteProject(project.title);
                      }
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </div>
                  <div 
                    className="flex flex-col"
                    onClick={() => handleProjectCardClick(project)}
                  >
                    <div className="h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center mb-4 mx-auto">
                      <span className="text-2xl text-indigo-600 font-medium">
                        {(() => {
                          try {
                            // Get initials, handle various edge cases
                            if (!project.title || typeof project.title !== 'string') {
                              return 'PR';
                            }
                            const words = project.title.split(' ').filter(w => w.length > 0);
                            if (words.length === 0) return 'PR';
                            if (words.length === 1) return words[0].substring(0, 2).toUpperCase();
                            return (words[0][0] + words[1][0]).toUpperCase();
                          } catch (e) {
                            return 'PR';
                          }
                        })()}
                      </span>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-800 text-center">{project.title}</h2>
                    <p className="text-gray-600 mt-1 text-center">{project.project_owner}</p>
                    
                    {/* Display location if available */}
                    {project.location && (
                      <p className="text-gray-500 mt-1 text-center text-sm">
                        {typeof project.location === 'string' ? project.location : JSON.stringify(project.location)}
                      </p>
                    )}
                    
                    {/* Display project type if available */}
                    {project.project_type && (
                      <p className="text-gray-500 mt-1 text-center text-sm">
                        <span className="font-medium">Type:</span> {
                          Array.isArray(project.project_type) 
                            ? project.project_type.join(', ')
                            : project.project_type
                        }
                      </p>
                    )}
                    
                    {/* Display year completed if available */}
                    {project.year_completed && typeof project.year_completed === 'object' && (
                      <p className="text-gray-500 mt-1 text-center text-sm">
                        <span className="font-medium">Completed:</span> {
                          project.year_completed.construction || 
                          project.year_completed.professional_services || 
                          Object.values(project.year_completed)[0]
                        }
                      </p>
                    )}
                    
                    {/* Display project description */}
                    <p className="text-gray-500 mt-3 text-sm line-clamp-3">{project.brief_description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </ErrorBoundary>
  )
} 