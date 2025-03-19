import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { API_URL } from '../lib/supabase'
import ChatButton from '../components/ChatButton'

interface Engineer {
  id: string;
  name: string;
  role: string;
  years_experience?: {
    Total?: string;
    "With Current Firm"?: string;
  };
  firm?: {
    Name?: string;
    Location?: string;
  };
  education: string;
  professional_registrations?: Array<{
    State?: string;
    License?: string;
  }>;
  other_qualifications?: string;
  relevant_projects?: Array<{
    "Title and Location"?: string;
    Description?: string;
    Role?: string;
    Fee?: string;
  }>;
}

const TeamPage = () => {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [engineers, setEngineers] = useState<Engineer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedEngineer, setSelectedEngineer] = useState<Engineer | null>(null)
  const [selectedEngineerDetails, setSelectedEngineerDetails] = useState<Engineer | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [detailsError, setDetailsError] = useState('')

  // Fetch all employees on component mount
  useEffect(() => {
    fetchAllEngineers()
  }, [])

  const fetchAllEngineers = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await fetch(`${API_URL}/api/employees`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch engineers')
      }
      
      const data = await response.json()
      setEngineers(Array.isArray(data) ? data : [])
      
      if (Array.isArray(data) && data.length === 0) {
        setError('No engineers found in the database')
      }
    } catch (err) {
      setError('An error occurred while fetching engineers. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }
      
      const data = await response.json()
      setEngineers(Array.isArray(data) ? data : [])
      
      if ((Array.isArray(data) && data.length === 0) || !data) {
        setError('No engineers found matching your criteria')
      }
    } catch (err) {
      setError('An error occurred while searching. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchEngineerDetails = async (engineerName: string) => {
    try {
      setLoadingDetails(true)
      setDetailsError('')
      
      const response = await fetch(`${API_URL}/api/employees/${encodeURIComponent(engineerName)}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch engineer details')
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      setDetailsError('An error occurred while fetching engineer details.')
      console.error(err)
      return null
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleEngineerClick = async (engineer: Engineer) => {
    setSelectedEngineer(engineer)
    
    // Fetch detailed information
    const details = await fetchEngineerDetails(engineer.name)
    if (details) {
      setSelectedEngineerDetails(details)
    }
  }

  const actions = [
    { id: 'all', label: 'All Employees', icon: '👥' },
    { id: 'add', label: 'Add Employee', icon: '➕' },
    { id: 'view', label: 'View Employee', icon: '👁️' },
    { id: 'update', label: 'Update Employee', icon: '🔄' },
    { id: 'delete', label: 'Delete Employee', icon: '🗑️' },
    { id: 'role', label: 'Employee Role', icon: '🏷️' },
  ]

  const handleActionClick = async (actionId: string) => {
    switch (actionId) {
      case 'all':
        await fetchAllEngineers();
        break;
      case 'add':
        alert('Add employee functionality to be implemented');
        break;
      case 'delete':
        if (selectedEngineer) {
          if (window.confirm(`Are you sure you want to delete ${selectedEngineer.name}?`)) {
            try {
              const response = await fetch(`${API_URL}/api/employees/${encodeURIComponent(selectedEngineer.name)}`, {
                method: 'DELETE'
              });
              
              if (response.ok) {
                alert(`${selectedEngineer.name} deleted successfully`);
                setSelectedEngineer(null);
                fetchAllEngineers();
              } else {
                alert('Failed to delete employee');
              }
            } catch (err) {
              console.error('Error deleting employee:', err);
              alert('Error deleting employee');
            }
          }
        } else {
          alert('Please select an employee first');
        }
        break;
      case 'role':
        const role = prompt('Enter role to filter by:');
        if (role) {
          try {
            setLoading(true);
            const response = await fetch(`${API_URL}/api/roles/${encodeURIComponent(role)}`);
            
            if (response.ok) {
              const data = await response.json();
              setEngineers(Array.isArray(data) ? data : []);
              
              if (Array.isArray(data) && data.length === 0) {
                setError(`No engineers found with role: ${role}`);
              }
            } else {
              setError(`Failed to find engineers with role: ${role}`);
            }
          } catch (err) {
            console.error('Error fetching by role:', err);
            setError('Error fetching engineers by role');
          } finally {
            setLoading(false);
          }
        }
        break;
      default:
        break;
    }
  }

  // Helper function to get experience in years
  const getExperienceYears = (engineer: Engineer) => {
    if (engineer.years_experience?.Total) {
      return engineer.years_experience.Total;
    }
    return 'N/A';
  }

  // Helper function to get education
  const getEducation = (engineer: Engineer) => {
    return engineer.education || 'Not specified';
  }

  // Helper function to get skills
  const getSkills = (engineer: Engineer) => {
    const skills = [];
    
    if (engineer.professional_registrations && engineer.professional_registrations.length > 0) {
      skills.push('Professional Engineer');
    }
    
    if (engineer.other_qualifications) {
      skills.push(engineer.other_qualifications);
    }
    
    if (engineer.firm?.Name) {
      skills.push(engineer.firm.Name);
    }
    
    return skills.length > 0 ? skills : ['No skills listed'];
  }

  // Helper function to get projects
  const getProjects = (engineer: Engineer) => {
    if (!engineer.relevant_projects || engineer.relevant_projects.length === 0) {
      return [];
    }
    
    return engineer.relevant_projects.map(project => 
      `${project["Title and Location"] || 'Unnamed Project'}: ${project.Description || 'No description'}`
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-white mb-6">Team Management</h1>

          {/* Search Bar */}
          <div className="glass p-6 mb-6">
            <form onSubmit={handleSearch} className="flex gap-4">
              <div className="flex-grow">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search for engineers by skills, role, or expertise..."
                  className="w-full px-4 py-3 glass border border-white border-opacity-20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-bright-purple"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-bright-purple text-white font-medium rounded-lg hover:bg-opacity-90 transition-colors focus:outline-none"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </form>
            
            {error && (
              <p className="mt-4 text-red-300">{error}</p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="glass-dark p-6 mb-6">
            {/* Button Row */}
            <div className="flex flex-wrap gap-4 mb-6">
              {actions.map((action) => (
                <button
                  key={action.id}
                  onClick={() => handleActionClick(action.id)}
                  className="px-4 py-2 glass hover:bg-white hover:bg-opacity-10 rounded-lg text-white transition-colors flex items-center"
                >
                  <span className="mr-2">{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>

            {/* Total Employees Counter */}
            <div className="glass p-4 rounded-lg">
              <p className="text-white font-medium">Total Employees: {engineers.length}</p>
            </div>
          </div>

          {/* Engineers List */}
          {loading ? (
            <div className="glass p-8 flex justify-center items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-bright-purple"></div>
            </div>
          ) : engineers.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {engineers.map((engineer) => (
                <motion.div
                  key={engineer.id || engineer.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className="glass p-6 cursor-pointer hover:bg-white hover:bg-opacity-5 transition-colors h-full flex flex-col"
                  onClick={() => handleEngineerClick(engineer)}
                >
                  <h3 className="text-xl font-semibold text-white">{engineer.name || 'Engineer'}</h3>
                  <p className="text-gray-300 mt-1">{engineer.role || 'Specialist'}</p>
                  
                  <div className="mt-4">
                    <p className="text-gray-400 text-sm">Experience</p>
                    <p className="text-white">{getExperienceYears(engineer)}</p>
                  </div>
                  
                  <div className="mt-3">
                    <p className="text-gray-400 text-sm">Education</p>
                    <p className="text-white truncate">{getEducation(engineer)}</p>
                  </div>
                  
                  <div className="mt-3 flex-grow">
                    <p className="text-gray-400 text-sm">Qualifications</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {getSkills(engineer).slice(0, 3).map((skill, index) => (
                        <span 
                          key={index} 
                          className="px-2 py-1 glass text-white text-xs rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                      {getSkills(engineer).length > 3 && (
                        <span className="px-2 py-1 text-gray-300 text-xs">
                          +{getSkills(engineer).length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <button
                    className="mt-4 px-4 py-2 glass text-white rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors w-full text-center"
                  >
                    View Profile
                  </button>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="glass p-8 text-center">
              <p className="text-gray-300">Search for engineers using the form above or use the action buttons to manage employees.</p>
              <p className="text-gray-400 mt-2 text-sm">Try searching for: "civil engineer", "machine learning", "project manager"</p>
            </div>
          )}
          
          {/* Engineer Details Modal */}
          {selectedEngineer && (
            <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="glass max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto"
              >
                {loadingDetails ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-bright-purple"></div>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h2 className="text-2xl font-bold text-white">{selectedEngineer.name || 'Engineer'}</h2>
                        <p className="text-gray-300 mt-1">{selectedEngineer.role || 'Specialist'}</p>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedEngineer(null);
                          setSelectedEngineerDetails(null);
                        }}
                        className="text-gray-300 hover:text-white"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    
                    {detailsError ? (
                      <div className="p-4 bg-red-500 bg-opacity-20 rounded-lg text-red-300 mb-6">
                        {detailsError}
                      </div>
                    ) : null}
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Experience</h3>
                        <p className="text-gray-300">{getExperienceYears(selectedEngineer)}</p>
                        
                        {selectedEngineer.firm && (
                          <div className="mt-4">
                            <h3 className="text-lg font-semibold text-white mb-2">Current Firm</h3>
                            <p className="text-gray-300">{selectedEngineer.firm.Name || 'Not specified'}</p>
                            <p className="text-gray-300">{selectedEngineer.firm.Location || ''}</p>
                          </div>
                        )}
                        
                        <h3 className="text-lg font-semibold text-white mt-6 mb-2">Education</h3>
                        <p className="text-gray-300">{getEducation(selectedEngineer)}</p>
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Professional Registrations</h3>
                        {selectedEngineer.professional_registrations && selectedEngineer.professional_registrations.length > 0 ? (
                          <div className="space-y-2">
                            {selectedEngineer.professional_registrations.map((reg, index) => (
                              <div key={index} className="glass p-2 rounded-lg">
                                <p className="text-gray-300">{reg.State || ''}: {reg.License || ''}</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-400">No registrations listed</p>
                        )}
                        
                        {selectedEngineer.other_qualifications && (
                          <div className="mt-6">
                            <h3 className="text-lg font-semibold text-white mb-2">Other Qualifications</h3>
                            <p className="text-gray-300">{selectedEngineer.other_qualifications}</p>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="mt-6">
                      <h3 className="text-lg font-semibold text-white mb-3">Relevant Projects</h3>
                      {selectedEngineer.relevant_projects && selectedEngineer.relevant_projects.length > 0 ? (
                        <div className="space-y-4">
                          {selectedEngineer.relevant_projects.map((project, index) => (
                            <div key={index} className="glass p-4 rounded-lg">
                              <h4 className="text-white font-medium">{project["Title and Location"] || 'Unnamed Project'}</h4>
                              <p className="text-gray-300 mt-2">{project.Description || 'No description provided'}</p>
                              {project.Role && (
                                <p className="text-gray-400 mt-2">Role: {project.Role}</p>
                              )}
                              {project.Fee && (
                                <p className="text-gray-400">Fee: {project.Fee}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-400">No projects listed</p>
                      )}
                    </div>
                    
                    <div className="mt-8 flex justify-end">
                      <button
                        onClick={() => {
                          setSelectedEngineer(null);
                          setSelectedEngineerDetails(null);
                        }}
                        className="px-4 py-2 glass text-white rounded-lg mr-3 hover:bg-white hover:bg-opacity-10 transition-colors"
                      >
                        Close
                      </button>
                      <button
                        className="px-4 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors"
                      >
                        Edit Profile
                      </button>
                    </div>
                  </>
                )}
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>
      
      <ChatButton />
    </div>
  )
}

export default TeamPage 