'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Employee {
  id?: string;
  name: string;
  role?: string;
}

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

export default function TeamsPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [employeeToDelete, setEmployeeToDelete] = useState<string>('')
  const [employeeToGet, setEmployeeToGet] = useState<string>('')
  const [showFileUpload, setShowFileUpload] = useState(false)
  const [showDeleteInput, setShowDeleteInput] = useState(false)
  const [showGetInput, setShowGetInput] = useState(false)
  const [showMergeForm, setShowMergeForm] = useState(false)
  const [sourceEmployee, setSourceEmployee] = useState<string>('')
  const [targetEmployee, setTargetEmployee] = useState<string>('')
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [employeeDetails, setEmployeeDetails] = useState<EmployeeDetail | null>(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)

  useEffect(() => {
    fetchEmployees()
  }, [])

  async function fetchEmployees() {
    try {
      setLoading(true)
      // Try to fetch from your API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('Fetching employees from:', `${apiUrl}/api/employees`)
      
      const response = await fetch(`${apiUrl}/api/employees`, {
        headers: { 'Accept': 'application/json' }
      })
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('API response:', data)
      
      // Extract employees from the response
      const employeeList = data.employees || data
      
      if (Array.isArray(employeeList) && employeeList.length > 0) {
        const mapped = employeeList.map((emp: any) => ({
          id: emp.id || emp.employee_name || emp.name,
          name: emp.employee_name || emp.name || 'Unknown',
          role: emp.role || (emp.resume_data && emp.resume_data.Role) || 'Employee'
        }))
        
        setEmployees(mapped)
        setError(null)
      } else {
        // Fallback to sample data if API returns empty array
        setError('No employees found')
      }
    } catch (err: any) {
      console.error('Error fetching employees:', err)
      setError(`Failed to load employees: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const uploadEmployee = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return
    
    try {
      setActionMessage(null)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      const response = await fetch(`${apiUrl}/api/employees`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`)
      
      const result = await response.json()
      setActionMessage({type: 'success', text: 'Employee added successfully'})
      setSelectedFile(null)
      setShowFileUpload(false)
      fetchEmployees() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error adding employee: ${err.message}`})
    }
  }

  const deleteEmployee = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!employeeToDelete) return
    
    try {
      setActionMessage(null)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${apiUrl}/api/employees/${encodeURIComponent(employeeToDelete)}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) throw new Error(`Delete failed: ${response.status}`)
      
      setActionMessage({type: 'success', text: 'Employee deleted successfully'})
      setEmployeeToDelete('')
      setShowDeleteInput(false)
      fetchEmployees() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error deleting employee: ${err.message}`})
    }
  }

  const handleEmployeeCardClick = async (employee: Employee) => {
    await fetchEmployeeDetails(employee.name);
  };

  async function fetchEmployeeDetails(employeeName: string) {
    try {
      setActionMessage(null)
      setLoading(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${apiUrl}/api/employees/${encodeURIComponent(employeeName)}`, {
        method: 'GET',
      })
      
      if (!response.ok) throw new Error(`Get details failed: ${response.status}`)
      
      const result = await response.json()
      
      // Log the structure to understand format issues
      console.log('Employee details:', result)
      
      setEmployeeDetails(result)
      setShowDetailsModal(true)
      setActionMessage({
        type: 'success', 
        text: `Retrieved details for ${result.employee_name || result.name}`
      })
    } catch (err: any) {
      console.error('Error fetching employee details:', err)
      setActionMessage({type: 'error', text: `Error getting employee details: ${err.message}`})
    } finally {
      setLoading(false)
    }
  }

  const getEmployeeDetails = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!employeeToGet) return
    await fetchEmployeeDetails(employeeToGet)
    setEmployeeToGet('')
    setShowGetInput(false)
  }

  const mergeEmployees = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceEmployee || !targetEmployee) return
    
    try {
      setActionMessage(null)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${apiUrl}/api/employees/merge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_employee: sourceEmployee,
          target_employee: targetEmployee
        }),
      })
      
      if (!response.ok) throw new Error(`Merge failed: ${response.status}`)
      
      const result = await response.json()
      setActionMessage({type: 'success', text: 'Employees merged successfully'})
      setSourceEmployee('')
      setTargetEmployee('')
      setShowMergeForm(false)
      fetchEmployees() // Refresh the list
    } catch (err: any) {
      setActionMessage({type: 'error', text: `Error merging employees: ${err.message}`})
    }
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
                setShowGetInput(false)
                setShowMergeForm(false)
              }}
              className="rounded-sm bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Add Employee
            </button>
            
            <button
              type="button"
              onClick={() => {
                setShowGetInput(!showGetInput)
                setShowFileUpload(false)
                setShowDeleteInput(false)
                setShowMergeForm(false)
              }}
              className="rounded-md bg-white/10 px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            >
              Get Employee
            </button>
            
            <button
              type="button"
              onClick={() => {
                setShowDeleteInput(!showDeleteInput)
                setShowFileUpload(false)
                setShowGetInput(false)
                setShowMergeForm(false)
              }}
              className="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-xs hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
            >
              Delete Employee
            </button>
            
            <button
              type="button"
              onClick={() => {
                setShowMergeForm(!showMergeForm)
                setShowFileUpload(false)
                setShowDeleteInput(false)
                setShowGetInput(false)
              }}
              className="rounded-md bg-amber-600 px-2.5 py-1.5 text-sm font-semibold text-white shadow-xs hover:bg-amber-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600"
            >
              Merge Employees
            </button>
          </div>
          
          {showFileUpload && (
            <form onSubmit={uploadEmployee} className="bg-white p-4 rounded-md shadow">
              <div className="mb-4">
                <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700">
                  Upload Resume (PDF)
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
          
          {showDeleteInput && (
            <form onSubmit={deleteEmployee} className="bg-white p-4 rounded-md shadow">
              <div className="mb-4">
                <label htmlFor="employee-name" className="block text-sm font-medium text-gray-700">
                  Employee Name to Delete
                </label>
                <input
                  id="employee-name"
                  name="employee-name"
                  type="text"
                  value={employeeToDelete}
                  onChange={(e) => setEmployeeToDelete(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter exact employee name"
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!employeeToDelete}
                  className="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            </form>
          )}
          
          {showGetInput && (
            <form onSubmit={getEmployeeDetails} className="bg-white p-4 rounded-md shadow">
              <div className="mb-4">
                <label htmlFor="employee-name-get" className="block text-sm font-medium text-gray-700">
                  Employee Name to Retrieve
                </label>
                <input
                  id="employee-name-get"
                  name="employee-name-get"
                  type="text"
                  value={employeeToGet}
                  onChange={(e) => setEmployeeToGet(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter exact employee name"
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!employeeToGet}
                  className="rounded-md bg-gray-900 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900 disabled:opacity-50"
                >
                  Get Details
                </button>
              </div>
            </form>
          )}
          
          {showMergeForm && (
            <form onSubmit={mergeEmployees} className="bg-white p-4 rounded-md shadow">
              <div className="mb-4">
                <label htmlFor="source-employee" className="block text-sm font-medium text-gray-700">
                  Source Employee Name (will be merged from)
                </label>
                <input
                  id="source-employee"
                  name="source-employee"
                  type="text"
                  value={sourceEmployee}
                  onChange={(e) => setSourceEmployee(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter exact employee name"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="target-employee" className="block text-sm font-medium text-gray-700">
                  Target Employee Name (will be merged into)
                </label>
                <input
                  id="target-employee"
                  name="target-employee"
                  type="text"
                  value={targetEmployee}
                  onChange={(e) => setTargetEmployee(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter exact employee name"
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!sourceEmployee || !targetEmployee}
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
        </div>
        
        {showDetailsModal && employeeDetails && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl overflow-hidden max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 bg-gray-100 flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Employee Details
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
                    {employeeDetails.employee_name || employeeDetails.name}
                  </h4>
                  <p className="text-gray-600 text-lg">
                    {Array.isArray(employeeDetails.role) 
                      ? employeeDetails.role.join(', ') 
                      : employeeDetails.role || 'No role specified'}
                  </p>
                </div>

                <div className="space-y-6">
                  {employeeDetails.years_experience && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Experience</h5>
                      <p className="mt-1">{employeeDetails.years_experience} years</p>
                    </div>
                  )}

                  {employeeDetails.firm_name_and_location && employeeDetails.firm_name_and_location.length > 0 && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Firm</h5>
                      <div className="mt-1">
                        {employeeDetails.firm_name_and_location.map((firm, idx) => (
                          <p key={idx} className="text-gray-800">{firm}</p>
                        ))}
                      </div>
                    </div>
                  )}

                  {employeeDetails.education && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Education</h5>
                      {Array.isArray(employeeDetails.education) ? (
                        <ul className="mt-1 list-disc list-inside">
                          {employeeDetails.education.map((edu, idx) => (
                            <li key={idx} className="text-gray-800">{edu}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-1 text-gray-800">{employeeDetails.education}</p>
                      )}
                    </div>
                  )}

                  {employeeDetails.current_professional_registration && 
                   employeeDetails.current_professional_registration.length > 0 && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Professional Registrations</h5>
                      <ul className="mt-1 list-disc list-inside">
                        {employeeDetails.current_professional_registration.map((reg, idx) => (
                          <li key={idx} className="text-gray-800">{reg}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {employeeDetails.other_professional_qualifications && 
                   employeeDetails.other_professional_qualifications.length > 0 && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Other Qualifications</h5>
                      <div className="mt-1 space-y-2">
                        {employeeDetails.other_professional_qualifications.map((qual, idx) => (
                          <p key={idx} className="text-gray-800">{qual}</p>
                        ))}
                      </div>
                    </div>
                  )}

                  {employeeDetails.relevant_projects && 
                   employeeDetails.relevant_projects.length > 0 && (
                    <div>
                      <h5 className="text-lg font-semibold text-gray-900">Relevant Projects</h5>
                      <div className="mt-2 space-y-4">
                        {employeeDetails.relevant_projects.map((project, idx) => (
                          <div key={idx} className="border border-gray-200 rounded-md p-4">
                            <h6 className="font-medium text-lg">
                              {project.title_and_location && project.title_and_location[0]}
                            </h6>
                            {project.title_and_location && project.title_and_location[1] && (
                              <p className="text-gray-600">{project.title_and_location[1]}</p>
                            )}
                            
                            <div className="mt-2 grid grid-cols-2 gap-2">
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
                    <div className="space-y-4">
                      {employeeDetails.resume_data["Years of Experience"] && (
                        <div>
                          <h5 className="font-semibold text-gray-900">Experience</h5>
                          <div className="mt-1 grid grid-cols-2 gap-2">
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

                      {/* ... other resume_data fields ... */}
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
        
        <h1 className="text-2xl font-bold mb-6">Team Members</h1>

        {loading ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-gray-600">Loading employees...</p>
          </div>
        ) : error ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => fetchEmployees()}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {employees.map((employee) => (
              <div 
                key={employee.id || employee.name} 
                className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleEmployeeCardClick(employee)}
              >
                <div className="flex flex-col items-center">
                  <div className="h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center mb-4">
                    <span className="text-2xl text-indigo-600 font-medium">
                      {employee.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800">{employee.name}</h2>
                  <p className="text-gray-600 mt-1">{employee.role}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
} 