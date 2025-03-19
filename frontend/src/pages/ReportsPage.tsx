import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import ChatButton from '../components/ChatButton'

interface Report {
  id: string;
  title: string;
  type: string;
  date: string;
  status: 'pending' | 'complete' | 'archived';
  summary: string;
}

const ReportsPage = () => {
  const { user } = useAuth()
  const [reports, setReports] = useState<Report[]>([
    {
      id: '1',
      title: 'Q2 Hiring Progress',
      type: 'Quarterly',
      date: '2023-06-30',
      status: 'complete',
      summary: 'Summary of all engineering hires during Q2 2023, including skills breakdown and hiring trends.'
    },
    {
      id: '2',
      title: 'Employee Skill Gap Analysis',
      type: 'Annual',
      date: '2023-12-15',
      status: 'pending',
      summary: 'Analysis of skill gaps in the current engineering team compared to project requirements.'
    },
    {
      id: '3',
      title: 'Retention Rate Analysis',
      type: 'Monthly',
      date: '2023-07-01',
      status: 'pending',
      summary: 'Monthly report on engineer retention rates and factors affecting turnover.'
    },
    {
      id: '4',
      title: 'Project Resource Allocation',
      type: 'Weekly',
      date: '2023-07-07',
      status: 'pending',
      summary: 'Weekly breakdown of engineering resource allocation across active projects.'
    },
    {
      id: '5',
      title: 'Training Program Effectiveness',
      type: 'Biannual',
      date: '2023-01-15',
      status: 'archived',
      summary: 'Analysis of the effectiveness of training programs on engineer productivity and skill growth.'
    }
  ])
  
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [activeFilter, setActiveFilter] = useState<string>('all')

  const filters = [
    { id: 'all', label: 'All Reports' },
    { id: 'pending', label: 'Pending' },
    { id: 'complete', label: 'Completed' },
    { id: 'archived', label: 'Archived' }
  ]

  const filteredReports = reports.filter(report => {
    if (activeFilter === 'all') return true
    return report.status === activeFilter
  })

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-white mb-6">Reports</h1>

          {/* Filters */}
          <div className="glass-dark p-6 mb-6">
            <div className="flex flex-wrap gap-4">
              {filters.map(filter => (
                <button
                  key={filter.id}
                  onClick={() => setActiveFilter(filter.id)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    activeFilter === filter.id
                      ? 'bg-bright-purple text-white'
                      : 'glass text-white hover:bg-white hover:bg-opacity-10'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Reports List */}
          <div className="space-y-4">
            {filteredReports.length === 0 ? (
              <div className="glass p-8 text-center">
                <p className="text-gray-300">No reports found for the selected filter.</p>
              </div>
            ) : (
              filteredReports.map((report, index) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="glass p-6 cursor-pointer hover:bg-white hover:bg-opacity-5 transition-colors"
                  onClick={() => setSelectedReport(report)}
                >
                  <div className="flex flex-col md:flex-row md:justify-between md:items-center">
                    <div>
                      <h3 className="text-xl font-semibold text-white">{report.title}</h3>
                      <p className="text-gray-300 mt-1">{report.type} Report</p>
                    </div>
                    <div className="mt-4 md:mt-0 flex items-center">
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        report.status === 'complete' ? 'bg-green-500 bg-opacity-20 text-green-300' :
                        report.status === 'pending' ? 'bg-yellow-500 bg-opacity-20 text-yellow-300' :
                        'bg-gray-500 bg-opacity-20 text-gray-300'
                      }`}>
                        {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                      </span>
                      <span className="ml-4 text-gray-400">{report.date}</span>
                    </div>
                  </div>
                  <p className="mt-4 text-gray-300">{report.summary}</p>
                  <div className="mt-4 flex justify-end">
                    <button
                      className="px-4 py-2 glass text-white rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
                    >
                      View Report
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </div>

          {/* Report Detail Modal */}
          {selectedReport && (
            <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="glass max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedReport.title}</h2>
                    <p className="text-gray-300 mt-1">{selectedReport.type} Report</p>
                  </div>
                  <button
                    onClick={() => setSelectedReport(null)}
                    className="text-gray-300 hover:text-white"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="mb-6">
                  <div className="flex flex-wrap gap-4 mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      selectedReport.status === 'complete' ? 'bg-green-500 bg-opacity-20 text-green-300' :
                      selectedReport.status === 'pending' ? 'bg-yellow-500 bg-opacity-20 text-yellow-300' :
                      'bg-gray-500 bg-opacity-20 text-gray-300'
                    }`}>
                      {selectedReport.status.charAt(0).toUpperCase() + selectedReport.status.slice(1)}
                    </span>
                    <span className="px-3 py-1 glass text-white text-sm rounded-full">
                      Date: {selectedReport.date}
                    </span>
                  </div>
                  
                  <p className="text-gray-300">{selectedReport.summary}</p>
                </div>
                
                <div className="glass-dark p-6 mb-6">
                  <p className="text-white">Report content would appear here. This is a placeholder for the actual report data.</p>
                  <p className="text-gray-400 mt-4">This report template includes sections for data visualization, key metrics, and actionable insights.</p>
                </div>
                
                <div className="mt-8 flex justify-end">
                  <button
                    onClick={() => setSelectedReport(null)}
                    className="px-4 py-2 glass text-white rounded-lg mr-3 hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    className="px-4 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors"
                  >
                    Download PDF
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>
      
      <ChatButton />
    </div>
  )
}

export default ReportsPage 