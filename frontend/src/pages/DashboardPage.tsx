import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { API_URL } from '../lib/supabase'

interface Engineer {
  id: string
  name: string
  role: string
  experience: number
  education: string
  skills: string[]
  projects: string[]
}

const DashboardPage = () => {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Engineer[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedEngineer, setSelectedEngineer] = useState<Engineer | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      const response = await fetch(`${API_URL}/query?query=${encodeURIComponent(query)}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }
      
      const data = await response.json()
      setResults(data.results || [])
      
      if (data.results?.length === 0) {
        setError('No engineers found matching your criteria')
      }
    } catch (err) {
      setError('An error occurred while searching. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-white mb-2">Engineer Search</h1>
          <p className="text-gray-300 mb-8">Find the perfect engineer for your project</p>

          <div className="glass p-6 mb-8">
            <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
              <div className="flex-grow">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search for engineers by skills, role, or expertise..."
                  className="w-full px-4 py-3 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-30"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 bg-bright-purple text-white font-medium rounded-lg hover:bg-opacity-90 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-bright-purple disabled:opacity-50"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </form>
            
            {error && (
              <p className="mt-4 text-red-300">{error}</p>
            )}
            
            <div className="mt-4">
              <p className="text-gray-300 text-sm">
                Try searching for: "civil engineer", "machine learning", "project manager"
              </p>
            </div>
          </div>

          {results.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.map((engineer) => (
                <motion.div
                  key={engineer.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className="glass p-6 cursor-pointer hover:bg-white hover:bg-opacity-5 transition-colors"
                  onClick={() => setSelectedEngineer(engineer)}
                >
                  <h3 className="text-xl font-semibold text-white">{engineer.name || 'Engineer'}</h3>
                  <p className="text-gray-300 mt-1">{engineer.role || 'Specialist'}</p>
                  
                  <div className="mt-4">
                    <p className="text-gray-400 text-sm">Experience</p>
                    <p className="text-white">{engineer.experience} years</p>
                  </div>
                  
                  <div className="mt-3">
                    <p className="text-gray-400 text-sm">Education</p>
                    <p className="text-white">{engineer.education || 'Not specified'}</p>
                  </div>
                  
                  <div className="mt-3">
                    <p className="text-gray-400 text-sm">Skills</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {engineer.skills?.slice(0, 3).map((skill, index) => (
                        <span 
                          key={index} 
                          className="px-2 py-1 bg-white bg-opacity-10 text-white text-xs rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                      {engineer.skills?.length > 3 && (
                        <span className="px-2 py-1 text-gray-300 text-xs">
                          +{engineer.skills.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <button
                    className="mt-4 px-4 py-2 bg-bright-purple bg-opacity-70 text-white text-sm rounded-lg hover:bg-opacity-100 transition-colors w-full"
                  >
                    View Profile
                  </button>
                </motion.div>
              ))}
            </div>
          )}
          
          {selectedEngineer && (
            <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="glass max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedEngineer.name || 'Engineer'}</h2>
                    <p className="text-gray-300 mt-1">{selectedEngineer.role || 'Specialist'}</p>
                  </div>
                  <button
                    onClick={() => setSelectedEngineer(null)}
                    className="text-gray-300 hover:text-white"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Experience</h3>
                    <p className="text-gray-300">{selectedEngineer.experience} years</p>
                    
                    <h3 className="text-lg font-semibold text-white mt-6 mb-2">Education</h3>
                    <p className="text-gray-300">{selectedEngineer.education || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedEngineer.skills?.map((skill, index) => (
                        <span 
                          key={index} 
                          className="px-3 py-1 bg-white bg-opacity-10 text-white text-sm rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Projects</h3>
                  {selectedEngineer.projects?.length > 0 ? (
                    <div className="space-y-4">
                      {selectedEngineer.projects.map((project, index) => (
                        <div key={index} className="bg-white bg-opacity-10 p-4 rounded-lg">
                          <p className="text-gray-300">{project}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400">No projects listed</p>
                  )}
                </div>
                
                <div className="mt-8 flex justify-end">
                  <button
                    onClick={() => setSelectedEngineer(null)}
                    className="px-4 py-2 border border-white border-opacity-20 text-white rounded-lg mr-3 hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    className="px-4 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors"
                  >
                    Contact Engineer
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default DashboardPage 