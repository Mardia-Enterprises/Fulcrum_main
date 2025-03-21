'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Employee {
  id?: string;
  name: string;
  role?: string;
}

export default function TeamsPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
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

    fetchEmployees()
  }, [])

  return (
    <main className="py-10 lg:pl-72">
      <div className="px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold mb-6">Team Members</h1>

        {loading ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-gray-600">Loading employees...</p>
          </div>
        ) : error ? (
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => window.location.reload()}
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
                className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow"
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