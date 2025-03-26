'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import ErrorBoundary from '../../components/ErrorBoundary'
import { API_URL } from '../../services/api'

interface EmployeeDetail {
  employee_name?: string;
  id?: string;
  name?: string;
  role?: string | string[];
  education?: string | string[];
  years_experience?: number;
  relevant_projects?: Array<{
    fee?: string;
    cost?: string;
    role?: string[];
    scope?: string;
    title_and_location?: string[];
  }>;
  firm_name_and_location?: string[];
  current_professional_registration?: string[];
  other_professional_qualifications?: string[];
  resume_data?: any;
}

// Function to normalize project titles to handle discrepancies between employee project titles and project page titles
const normalizeProjectTitle = (title: string): string => {
  if (!title) return '';
  
  // Replace multiple spaces with a single space
  let normalized = title.replace(/\s+/g, ' ').trim();
  
  // Remove common punctuation that might differ between formats
  normalized = normalized.replace(/[,;:.]/g, ' ').replace(/\s+/g, ' ').trim();
  
  // Convert to lowercase for case-insensitive comparison
  return normalized.toLowerCase();
};

// Component for project links with better title handling
const ProjectLink = ({ projectTitle }: { projectTitle: string }) => {
  const [linkState, setLinkState] = useState<'default' | 'loading' | 'error'>('default');
  const router = useRouter();
  
  // Extract project name from title_and_location which might be formatted as:
  // "Project Name, Location" or just "Project Name"
  const cleanProjectTitle = projectTitle.trim();
  
  const handleProjectNavigation = (e: React.MouseEvent) => {
    e.preventDefault();
    setLinkState('loading');
    
    // Navigate to the project detail page
    router.push(`/projects/${encodeURIComponent(cleanProjectTitle)}`);
  };
  
  return (
    <button
      onClick={handleProjectNavigation}
      disabled={linkState === 'loading'}
      className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white 
        ${linkState === 'loading' ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700'} 
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
      title={`View details for project: ${cleanProjectTitle}`}
    >
      {linkState === 'loading' ? 'Loading...' : 'View Project Details'}
    </button>
  );
};

export default function EmployeeDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const employeeName = decodeURIComponent(params.name as string);
  
  const [employeeDetails, setEmployeeDetails] = useState<EmployeeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (employeeName) {
      fetchEmployeeDetails(employeeName);
    }
  }, [employeeName]);

  async function fetchEmployeeDetails(name: string) {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/employees/${encodeURIComponent(name)}`, {
        method: 'GET',
      });
      
      if (!response.ok) throw new Error(`Failed to load employee details: ${response.status}`);
      
      const result = await response.json();
      console.log('Employee details:', result);
      
      setEmployeeDetails(result);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching employee details:', err);
      setError(`Error loading employee details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link 
            href="/teams" 
            className="inline-flex items-center text-indigo-600 hover:text-indigo-900"
          >
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Team
          </Link>
        </div>

        {loading ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-gray-600">Loading employee details...</p>
          </div>
        ) : error ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => router.push('/teams')}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              Return to Team Page
            </button>
          </div>
        ) : employeeDetails ? (
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-200 bg-gray-50">
              <h1 className="text-2xl font-bold text-gray-900">
                {employeeDetails.employee_name || employeeDetails.name}
              </h1>
              <p className="text-gray-600 text-lg mt-1">
                {Array.isArray(employeeDetails.role) 
                  ? employeeDetails.role.join(', ') 
                  : employeeDetails.role || 'No role specified'}
              </p>
            </div>
            
            <div className="px-6 py-6">
              <div className="space-y-8">
                {employeeDetails.years_experience && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Experience</h2>
                    <p className="mt-2">{employeeDetails.years_experience} years</p>
                  </div>
                )}

                {employeeDetails.firm_name_and_location && employeeDetails.firm_name_and_location.length > 0 && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Firm</h2>
                    <div className="mt-2">
                      {employeeDetails.firm_name_and_location.map((firm, idx) => (
                        <p key={idx} className="text-gray-800">{firm}</p>
                      ))}
                    </div>
                  </div>
                )}

                {employeeDetails.education && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Education</h2>
                    {Array.isArray(employeeDetails.education) ? (
                      <ul className="mt-2 list-disc list-inside">
                        {employeeDetails.education.map((edu, idx) => (
                          <li key={idx} className="text-gray-800">{edu}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-gray-800">{employeeDetails.education}</p>
                    )}
                  </div>
                )}

                {employeeDetails.current_professional_registration && 
                 employeeDetails.current_professional_registration.length > 0 && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Professional Registrations</h2>
                    <ul className="mt-2 list-disc list-inside">
                      {employeeDetails.current_professional_registration.map((reg, idx) => (
                        <li key={idx} className="text-gray-800">{reg}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {employeeDetails.other_professional_qualifications && 
                 employeeDetails.other_professional_qualifications.length > 0 && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Other Qualifications</h2>
                    <div className="mt-2 space-y-2">
                      {employeeDetails.other_professional_qualifications.map((qual, idx) => (
                        <p key={idx} className="text-gray-800">{qual}</p>
                      ))}
                    </div>
                  </div>
                )}

                {employeeDetails.relevant_projects && 
                 employeeDetails.relevant_projects.length > 0 && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Relevant Projects</h2>
                    <div className="mt-4 space-y-6">
                      {employeeDetails.relevant_projects.map((project, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-md p-4 hover:shadow-md transition-shadow">
                          <div className="flex flex-col md:flex-row md:items-start md:justify-between">
                            <div className="flex-1">
                              <h3 className="font-medium text-lg text-indigo-700">
                                {project.title_and_location && project.title_and_location[0]}
                              </h3>
                              {project.title_and_location && project.title_and_location[1] && (
                                <p className="text-gray-600">{project.title_and_location[1]}</p>
                              )}
                            </div>
                            
                            {project.title_and_location && project.title_and_location[0] && (
                              <div className="mt-3 md:mt-0 md:ml-4 flex-shrink-0">
                                <ProjectLink projectTitle={project.title_and_location[0]} />
                              </div>
                            )}
                          </div>
                          
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                            {project.role && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Role:</span>
                                <p>{Array.isArray(project.role) ? project.role.join(', ') : project.role}</p>
                              </div>
                            )}
                            
                            {project.fee && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Fee:</span>
                                <p>{project.fee}</p>
                              </div>
                            )}
                            
                            {project.cost && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Cost:</span>
                                <p>{project.cost}</p>
                              </div>
                            )}
                          </div>
                          
                          {project.scope && (
                            <div className="mt-3">
                              <span className="text-sm font-medium text-gray-500">Scope:</span>
                              <p className="mt-1 text-sm text-gray-800">{project.scope}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Fallback to resume_data if available */}
                {employeeDetails.resume_data && !employeeDetails.years_experience && (
                  <div className="space-y-6">
                    {employeeDetails.resume_data["Years of Experience"] && (
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">Experience</h2>
                        <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <span className="text-sm text-gray-500">Total:</span>
                            <p>{employeeDetails.resume_data["Years of Experience"].Total || 'N/A'}</p>
                          </div>
                          <div>
                            <span className="text-sm text-gray-500">With Current Firm:</span>
                            <p>{employeeDetails.resume_data["Years of Experience"]["With Current Firm"] || 'N/A'}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Additional resume data fields can be added here as needed */}
                  </div>
                )}

                {!employeeDetails.resume_data && 
                 !employeeDetails.education && 
                 !employeeDetails.relevant_projects && 
                 !employeeDetails.years_experience && (
                  <div className="p-4 bg-yellow-50 rounded-md">
                    <p className="text-yellow-700">Basic employee information only. No detailed resume data available.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-red-500">Employee not found</p>
            <button
              onClick={() => router.push('/teams')}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              Return to Team Page
            </button>
          </div>
        )}
      </div>
    </main>
  )
} 