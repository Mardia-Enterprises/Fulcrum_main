'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import ErrorBoundary from '../../components/ErrorBoundary'

interface Firm {
  firm_name?: string;
  firm_location?: string;
  role?: string;
  [key: string]: any;
}

interface ProjectDetail {
  id?: string;
  title_and_location?: string;
  year_completed?: {
    professional_services?: number;
    construction?: number;
    [key: string]: any;
  };
  project_owner?: string;
  point_of_contact_name?: string;
  point_of_contact_telephone_number?: string;
  brief_description?: string;
  firms_from_section_c_involved_with_this_project?: Array<Firm>;
  project_key?: string;
  file_id?: string;
  project_data?: any;
  
  project_fee?: string | number;
  project_cost?: string | number;
  construction_cost?: string | number;
  
  location?: string;
  city?: string;
  state?: string;
  
  project_type?: string | string[];
  category?: string | string[];
  
  start_date?: string | number;
  end_date?: string | number;
  
  client_contact?: string;
  client_email?: string;
  client_phone?: string;
  
  [key: string]: any;
}

// Helper to get the Projects API URL (port 8001)
const getProjectsApiUrl = () => {
  const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  // Replace port 8000 with 8001 for the Projects API
  return baseApiUrl.replace(':8000', ':8001').replace('8000', '8001')
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [projectDetails, setProjectDetails] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const projectTitle = typeof params.projectTitle === 'string' 
    ? decodeURIComponent(params.projectTitle) 
    : Array.isArray(params.projectTitle) 
      ? decodeURIComponent(params.projectTitle[0]) 
      : '';

  useEffect(() => {
    if (projectTitle) {
      fetchProjectDetails(projectTitle);
    }
  }, [projectTitle]);

  async function fetchProjectDetails(title: string) {
    try {
      setLoading(true)
      const projectsApiUrl = getProjectsApiUrl()
      
      const response = await fetch(`${projectsApiUrl}/api/projects/${encodeURIComponent(title)}`, {
        method: 'GET',
      })
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Project not found');
        }
        throw new Error(`Get details failed: ${response.status}`)
      }
      
      let result;
      try {
        result = await response.json()
        console.log('Project details:', result)
      } catch (jsonError) {
        console.error('Error parsing JSON response:', jsonError)
        throw new Error('Invalid response format from API')
      }
      
      // Check if the result is valid
      if (!result || typeof result !== 'object') {
        throw new Error('Invalid project data received')
      }
      
      // Create a sanitized project detail object by copying all properties safely
      const sanitizedDetails: ProjectDetail = {};
      
      // Process all fields from the API result
      Object.keys(result).forEach(key => {
        if (key === 'title_and_location') {
          sanitizedDetails.title_and_location = typeof result.title_and_location === 'string' 
            ? result.title_and_location : title;
        }
        else if (key === 'year_completed' && result.year_completed && typeof result.year_completed === 'object') {
          sanitizedDetails.year_completed = {};
          Object.keys(result.year_completed).forEach(yearKey => {
            if (typeof result.year_completed[yearKey] === 'number' || 
                typeof result.year_completed[yearKey] === 'string') {
              sanitizedDetails.year_completed![yearKey] = result.year_completed[yearKey];
            }
          });
        }
        else if (key === 'firms_from_section_c_involved_with_this_project' && 
                Array.isArray(result.firms_from_section_c_involved_with_this_project)) {
          sanitizedDetails.firms_from_section_c_involved_with_this_project = 
            result.firms_from_section_c_involved_with_this_project
              .filter((firm: any) => firm && typeof firm === 'object')
              .map((firm: any) => {
                const sanitizedFirm: Firm = {};
                Object.keys(firm).forEach(firmKey => {
                  if (typeof firm[firmKey] === 'string' || 
                      typeof firm[firmKey] === 'number' ||
                      Array.isArray(firm[firmKey])) {
                    sanitizedFirm[firmKey] = firm[firmKey];
                  }
                });
                // Ensure required fields have default values if missing
                sanitizedFirm.firm_name = sanitizedFirm.firm_name || 'Unknown Firm';
                return sanitizedFirm;
              });
        }
        else if (typeof result[key] === 'string' || 
                 typeof result[key] === 'number' || 
                 typeof result[key] === 'boolean') {
          // Handle primitive types directly
          sanitizedDetails[key] = result[key];
        }
        else if (Array.isArray(result[key])) {
          // Handle arrays (copy them)
          sanitizedDetails[key] = [...result[key]];
        }
        else if (result[key] && typeof result[key] === 'object') {
          // Handle nested objects (shallow copy)
          sanitizedDetails[key] = {...result[key]};
        }
      });
      
      setProjectDetails(sanitizedDetails)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching project details:', err)
      
      if (err.message.includes('Failed to fetch') || err.message.includes('Network error')) {
        setError(`Projects API is not running. Please make sure the backend Projects API is running on port 8001.`)
      } else if (err.message.includes('not found')) {
        setError(`Project "${title}" not found`)
      } else if (err.message.includes('validation error')) {
        setError(`Data validation error. The project data may be in an invalid format.`)
      } else {
        setError(`Error getting project details: ${err.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const deleteProject = async () => {
    if (!projectTitle) return
    
    const confirmed = window.confirm(`Are you sure you want to delete ${projectTitle}?`);
    if (!confirmed) return;
    
    try {
      setLoading(true)
      const projectsApiUrl = getProjectsApiUrl()
      
      const response = await fetch(`${projectsApiUrl}/api/projects/${encodeURIComponent(projectTitle)}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) throw new Error(`Delete failed: ${response.status}`)
      
      router.push('/projects'); // Redirect back to projects list
    } catch (err: any) {
      console.error('Error deleting project:', err)
      setError(`Error deleting project: ${err.message}`)
      setLoading(false)
    }
  }

  return (
    <ErrorBoundary>
      <main className="py-10 lg:pl-72">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="mb-8 flex justify-between items-center">
            <Link 
              href="/projects" 
              className="inline-flex items-center text-indigo-600 hover:text-indigo-800"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Projects
            </Link>
            {!error && <button
              onClick={deleteProject}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Project
            </button>}
          </div>

          {loading ? (
            <div className="bg-white shadow-md rounded-lg p-8 text-center">
              <p className="text-gray-600">Loading project details...</p>
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
              <Link href="/projects">
                <div className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
                  Back to Projects
                </div>
              </Link>
            </div>
          ) : projectDetails ? (
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h1 className="text-2xl font-bold text-gray-900">{projectDetails.title_and_location}</h1>
              </div>
              
              <div className="px-6 py-6 space-y-6">
                {projectDetails.project_owner && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Project Owner</h2>
                    <p className="mt-1 text-gray-700">{projectDetails.project_owner}</p>
                  </div>
                )}

                {projectDetails.year_completed && Object.keys(projectDetails.year_completed).length > 0 && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Year Completed</h2>
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(projectDetails.year_completed).map(([key, value]) => (
                        <div key={key} className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">
                            {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}:
                          </span>
                          <p className="mt-1 text-gray-900 font-medium">{value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(projectDetails.project_fee || projectDetails.project_cost || projectDetails.construction_cost) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Cost Information</h2>
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {projectDetails.project_fee && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Project Fee:</span>
                          <p className="mt-1 text-gray-900 font-medium">{projectDetails.project_fee}</p>
                        </div>
                      )}
                      {projectDetails.project_cost && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Project Cost:</span>
                          <p className="mt-1 text-gray-900 font-medium">{projectDetails.project_cost}</p>
                        </div>
                      )}
                      {projectDetails.construction_cost && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Construction Cost:</span>
                          <p className="mt-1 text-gray-900 font-medium">{projectDetails.construction_cost}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {projectDetails.point_of_contact_name && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Point of Contact</h2>
                    <div className="mt-2 bg-gray-50 p-4 rounded-md">
                      <p className="text-gray-900">{projectDetails.point_of_contact_name}</p>
                      {projectDetails.point_of_contact_telephone_number && (
                        <p className="mt-1 text-gray-700">{projectDetails.point_of_contact_telephone_number}</p>
                      )}
                    </div>
                  </div>
                )}

                {projectDetails.brief_description && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Description</h2>
                    <div className="mt-2 p-4 bg-gray-50 rounded-md">
                      <p className="text-gray-700 whitespace-pre-line">{projectDetails.brief_description}</p>
                    </div>
                  </div>
                )}

                {(projectDetails.project_type || projectDetails.category) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Project Classification</h2>
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {projectDetails.project_type && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Project Type:</span>
                          <p className="mt-1 text-gray-900">
                            {Array.isArray(projectDetails.project_type) 
                              ? projectDetails.project_type.join(', ')
                              : projectDetails.project_type}
                          </p>
                        </div>
                      )}
                      {projectDetails.category && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Category:</span>
                          <p className="mt-1 text-gray-900">
                            {Array.isArray(projectDetails.category) 
                              ? projectDetails.category.join(', ')
                              : projectDetails.category}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {(projectDetails.start_date || projectDetails.end_date) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Project Timeline</h2>
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {projectDetails.start_date && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">Start Date:</span>
                          <p className="mt-1 text-gray-900 font-medium">{projectDetails.start_date}</p>
                        </div>
                      )}
                      {projectDetails.end_date && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <span className="text-sm font-medium text-gray-500">End Date:</span>
                          <p className="mt-1 text-gray-900 font-medium">{projectDetails.end_date}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {(projectDetails.client_contact || projectDetails.client_email || projectDetails.client_phone) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Client Information</h2>
                    <div className="mt-2 bg-gray-50 p-4 rounded-md">
                      {projectDetails.client_contact && (
                        <p className="text-gray-900">Contact: {projectDetails.client_contact}</p>
                      )}
                      {projectDetails.client_email && (
                        <p className="mt-1 text-gray-700">Email: {projectDetails.client_email}</p>
                      )}
                      {projectDetails.client_phone && (
                        <p className="mt-1 text-gray-700">Phone: {projectDetails.client_phone}</p>
                      )}
                    </div>
                  </div>
                )}

                {(() => {
                  const excludedFields = [
                    'id', 'title_and_location', 'year_completed', 'project_owner',
                    'point_of_contact_name', 'point_of_contact_telephone_number',
                    'brief_description', 'firms_from_section_c_involved_with_this_project',
                    'project_fee', 'project_cost', 'construction_cost', 'project_type',
                    'category', 'start_date', 'end_date', 'client_contact', 'client_email',
                    'client_phone', 'project_key', 'file_id', 'project_data'
                  ];
                  
                  const additionalFields = Object.entries(projectDetails)
                    .filter(([key]) => !excludedFields.includes(key))
                    .filter(([_, value]) => 
                      value !== null && 
                      value !== undefined && 
                      value !== '' &&
                      !((typeof value === 'object') && Object.keys(value).length === 0)
                    );
                  
                  if (additionalFields.length === 0) return null;
                  
                  return (
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">Additional Information</h2>
                      <div className="mt-2 grid grid-cols-1 gap-4">
                        {additionalFields.map(([key, value]) => {
                          // Format the display of the value based on its type
                          let displayValue;
                          
                          if (key === 'budget' && typeof value === 'string') {
                            try {
                              // Try to parse budget as JSON
                              const budgetObj = JSON.parse(value);
                              displayValue = (
                                <div className="space-y-2">
                                  {Object.entries(budgetObj).map(([budgetKey, budgetValue]) => (
                                    <div key={budgetKey} className="flex">
                                      <span className="text-sm text-gray-600 capitalize mr-2">
                                        {budgetKey.replace(/_/g, ' ')}:
                                      </span>
                                      <span>{String(budgetValue)}</span>
                                    </div>
                                  ))}
                                </div>
                              );
                            } catch (e) {
                              // If not valid JSON, display as is
                              displayValue = value;
                            }
                          } else if (key.includes('personnel') && typeof value === 'string') {
                            try {
                              // Try to parse personnel as JSON
                              const personnelArray = JSON.parse(value);
                              if (Array.isArray(personnelArray)) {
                                displayValue = (
                                  <div className="space-y-3">
                                    {personnelArray.map((person, idx) => (
                                      <div key={idx} className="bg-gray-50 p-2 rounded">
                                        {Object.entries(person).map(([personKey, personValue]) => (
                                          <div key={personKey} className="flex flex-wrap">
                                            <span className="text-sm text-gray-600 capitalize mr-2">
                                              {personKey.replace(/_/g, ' ')}:
                                            </span>
                                            <span>{String(personValue)}</span>
                                          </div>
                                        ))}
                                      </div>
                                    ))}
                                  </div>
                                );
                              } else {
                                displayValue = String(value);
                              }
                            } catch (e) {
                              // If not valid JSON, display as is
                              displayValue = value;
                            }
                          } else if (typeof value === 'object') {
                            // Handle other objects
                            displayValue = (
                              <div className="space-y-1">
                                {Object.entries(value).map(([objKey, objValue]) => (
                                  <div key={objKey} className="flex flex-wrap">
                                    <span className="text-sm text-gray-600 capitalize mr-2">
                                      {objKey.replace(/_/g, ' ')}:
                                    </span>
                                    <span>{typeof objValue === 'object' ? JSON.stringify(objValue) : String(objValue)}</span>
                                  </div>
                                ))}
                              </div>
                            );
                          } else {
                            // Simple string or number
                            displayValue = String(value);
                          }
                          
                          return (
                            <div key={key} className="bg-gray-50 p-3 rounded-md">
                              <span className="text-sm font-medium text-gray-500">
                                {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}:
                              </span>
                              <div className="mt-1 text-gray-900">
                                {displayValue}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })()}

                {projectDetails.firms_from_section_c_involved_with_this_project && 
                 projectDetails.firms_from_section_c_involved_with_this_project.length > 0 && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Firms Involved</h2>
                    <div className="mt-2 space-y-4">
                      {projectDetails.firms_from_section_c_involved_with_this_project.map((firm, idx) => (
                        <div key={idx} className="border border-gray-200 bg-gray-50 rounded-md p-4">
                          <h3 className="font-medium text-lg text-gray-900">
                            {firm.firm_name}
                          </h3>
                          {firm.firm_location && (
                            <p className="text-gray-600 mt-1">{firm.firm_location}</p>
                          )}
                          
                          {firm.role && (
                            <div className="mt-3">
                              <span className="text-sm font-medium text-gray-500">Role:</span>
                              <p className="mt-1 text-gray-700">{firm.role}</p>
                            </div>
                          )}
                          
                          {Object.entries(firm)
                            .filter(([key]) => !['firm_name', 'firm_location', 'role'].includes(key))
                            .map(([key, value]) => (
                              <div key={key} className="mt-3">
                                <span className="text-sm font-medium text-gray-500">
                                  {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}:
                                </span>
                                <p className="mt-1 text-gray-700">
                                  {typeof value === 'object' 
                                    ? JSON.stringify(value) 
                                    : String(value)}
                                </p>
                              </div>
                            ))
                          }
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white shadow-md rounded-lg p-8 text-center">
              <p className="text-amber-500">No project details found</p>
              <Link href="/projects">
                <div className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
                  Back to Projects
                </div>
              </Link>
            </div>
          )}
        </div>
      </main>
    </ErrorBoundary>
  )
} 