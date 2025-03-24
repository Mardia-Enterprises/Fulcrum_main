'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Project {
  id?: string;
  title: string;
  brief_description?: string;
  project_owner?: string;
}

interface ProjectDetail {
  id?: string;
  title_and_location?: string;
  year_completed?: {
    professional_services?: number;
    construction?: number;
  };
  project_owner?: string;
  point_of_contact_name?: string;
  point_of_contact_telephone_number?: string;
  brief_description?: string;
  firms_from_section_c_involved_with_this_project?: Array<{
    firm_name?: string;
    firm_location?: string;
    role?: string;
  }>;
}

export default function ProjectsPage() {
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
  const [projectDetails, setProjectDetails] = useState<ProjectDetail | null>(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [projectTitle, setProjectTitle] = useState<string>('')

  useEffect(() => {
    fetchProjects()
  }, [])

  async function fetchProjects() {
    try {
      setLoading(true)
      // Try to fetch from your API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      console.log('Fetching projects from:', `${apiUrl}/api/projects`)
      
      const response = await fetch(`${apiUrl}/api/projects`, {
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
        const mapped = projectsList.map((proj: any) => ({
          id: proj.id || proj.project_key || proj.title_and_location,
          title: proj.title_and_location || proj.project_key || 'Unknown',
          brief_description: proj.brief_description || 'No description available',
          project_owner: proj.project_owner || 'Unknown'
        }))
        
        setProjects(mapped)
        setError(null)
      } else {
        // Fallback to sample data if API returns empty array
        setError('No projects found')
      }
    } catch (err: any) {
      console.error('Error fetching projects:', err)
      setError(`Failed to load projects: ${err.message}`)
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (projectTitle) {
        formData.append('project_title', projectTitle)
      }
      
      const response = await fetch(`${apiUrl}/api/projects`, {
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      
      const response = await fetch(`${apiUrl}/api/projects/${encodeURIComponent(projectTitle)}`, {
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

  const handleProjectCardClick = async (project: Project) => {
    await fetchProjectDetails(project.title);
  };

  async function fetchProjectDetails(projectTitle: string) {
    try {
      setActionMessage(null)
      setLoading(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      
      const response = await fetch(`${apiUrl}/api/projects/${encodeURIComponent(projectTitle)}`, {
        method: 'GET',
      })
      
      if (!response.ok) throw new Error(`Get details failed: ${response.status}`)
      
      const result = await response.json()
      
      // Log the structure to understand format issues
      console.log('Project details:', result)
      
      setProjectDetails(result)
      setShowDetailsModal(true)
      setActionMessage({
        type: 'success', 
        text: `Retrieved details for ${result.title_and_location || result.project_key}`
      })
    } catch (err: any) {
      console.error('Error fetching project details:', err)
      setActionMessage({type: 'error', text: `Error getting project details: ${err.message}`})
    } finally {
      setLoading(false)
    }
  }

  const mergeProjects = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceProject || !targetProject) return
    
    try {
      setActionMessage(null)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      
      const response = await fetch(`${apiUrl}/api/merge_projects?source_title=${encodeURIComponent(sourceProject)}&target_title=${encodeURIComponent(targetProject)}`, {
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      
      const response = await fetch(`${apiUrl}/api/query`, {
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
        const mapped = projectsList.map((proj: any) => ({
          id: proj.id || proj.project_key || proj.title_and_location,
          title: proj.title_and_location || proj.project_key || 'Unknown',
          brief_description: proj.brief_description || 'No description available',
          project_owner: proj.project_owner || 'Unknown'
        }))
        
        setProjects(mapped)
        setActionMessage({type: 'success', text: `Found ${mapped.length} projects matching your query`})
        setError(null)
      } else {
        setProjects([])
        setActionMessage({type: 'error', text: 'No projects found matching your query'})
      }
    } catch (err: any) {
      console.error('Error searching projects:', err)
      setActionMessage({type: 'error', text: `Search failed: ${err.message}`})
    } finally {
      setLoading(false)
    }
  }

  const resetSearch = () => {
    setSearchQuery('')
    fetchProjects()
  }

  return (
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
        
        {showDetailsModal && projectDetails && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl overflow-hidden max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 bg-gray-100 flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Project Details
                </h3>
                <button 
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="px-6 py-4">
                <div className="mb-6">
                  <h4 className="text-2xl font-bold">
                    {projectDetails.title_and_location}
                  </h4>
                </div>

                <div className="space-y-6">
                  {projectDetails.project_owner && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Project Owner</h5>
                      <p className="mt-1">{projectDetails.project_owner}</p>
                    </div>
                  )}

                  {projectDetails.year_completed && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Year Completed</h5>
                      <div className="mt-1 grid grid-cols-2 gap-2">
                        {projectDetails.year_completed.professional_services && (
                          <div>
                            <span className="text-sm font-medium text-gray-500">Professional Services:</span>
                            <p>{projectDetails.year_completed.professional_services}</p>
                          </div>
                        )}
                        {projectDetails.year_completed.construction && (
                          <div>
                            <span className="text-sm font-medium text-gray-500">Construction:</span>
                            <p>{projectDetails.year_completed.construction}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {projectDetails.point_of_contact_name && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Point of Contact</h5>
                      <p className="mt-1">{projectDetails.point_of_contact_name}</p>
                      {projectDetails.point_of_contact_telephone_number && (
                        <p className="mt-1">{projectDetails.point_of_contact_telephone_number}</p>
                      )}
                    </div>
                  )}

                  {projectDetails.brief_description && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Description</h5>
                      <p className="mt-1 text-gray-800">{projectDetails.brief_description}</p>
                    </div>
                  )}

                  {projectDetails.firms_from_section_c_involved_with_this_project && 
                   projectDetails.firms_from_section_c_involved_with_this_project.length > 0 && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Firms Involved</h5>
                      <div className="mt-2 space-y-4">
                        {projectDetails.firms_from_section_c_involved_with_this_project.map((firm, idx) => (
                          <div key={idx} className="border border-gray-200 rounded-md p-4">
                            <h6 className="font-medium text-lg">
                              {firm.firm_name}
                            </h6>
                            {firm.firm_location && (
                              <p className="text-gray-600">{firm.firm_location}</p>
                            )}
                            
                            {firm.role && (
                              <div className="mt-2">
                                <span className="text-sm font-medium text-gray-500">Role:</span>
                                <p>{firm.role}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="bg-gray-50 px-6 py-3 flex justify-end">
                <button
                  type="button"
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  onClick={() => setShowDetailsModal(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
        
        <h1 className="text-2xl font-bold mb-6">Projects</h1>

        {loading ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-gray-600">Loading projects...</p>
          </div>
        ) : error ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-red-500">{error}</p>
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
                      {project.title.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800 text-center">{project.title}</h2>
                  <p className="text-gray-600 mt-1 text-center">{project.project_owner}</p>
                  <p className="text-gray-500 mt-3 text-sm line-clamp-3">{project.brief_description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
} 