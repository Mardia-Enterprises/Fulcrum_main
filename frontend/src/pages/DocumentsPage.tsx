import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import ChatButton from '../components/ChatButton'

interface Document {
  id: string;
  title: string;
  type: string;
  lastModified: string;
  owner: string;
  size: string;
  shared: boolean;
}

const DocumentsPage = () => {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: '1',
      title: 'Engineering Onboarding Guide',
      type: 'PDF',
      lastModified: '2023-07-10',
      owner: 'HR Department',
      size: '2.3 MB',
      shared: true
    },
    {
      id: '2',
      title: 'Software Development Best Practices',
      type: 'DOCX',
      lastModified: '2023-06-15',
      owner: 'Tech Lead',
      size: '1.7 MB',
      shared: true
    },
    {
      id: '3',
      title: 'Project Timeline Q3',
      type: 'XLSX',
      lastModified: '2023-07-01',
      owner: 'Project Manager',
      size: '950 KB',
      shared: false
    },
    {
      id: '4',
      title: 'Engineering Team Structure',
      type: 'PDF',
      lastModified: '2023-05-22',
      owner: 'CTO',
      size: '1.2 MB',
      shared: true
    },
    {
      id: '5',
      title: 'Annual Budget Allocation',
      type: 'XLSX',
      lastModified: '2023-01-15',
      owner: 'Finance Dept',
      size: '3.5 MB',
      shared: false
    }
  ])
  
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilterType, setActiveFilterType] = useState<string>('all')

  const documentTypes = ['all', 'PDF', 'DOCX', 'XLSX', 'TXT', 'PPT']

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = activeFilterType === 'all' || doc.type === activeFilterType
    return matchesSearch && matchesType
  })

  const handleUpload = () => {
    alert('Upload functionality would be implemented here')
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-white">Documents</h1>
            <button 
              onClick={handleUpload}
              className="px-4 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors"
            >
              Upload Document
            </button>
          </div>

          {/* Search and Filter */}
          <div className="glass p-6 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-grow">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search documents..."
                  className="w-full px-4 py-3 glass border border-white border-opacity-20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-bright-purple"
                />
              </div>
              <div className="flex-shrink-0">
                <select
                  value={activeFilterType}
                  onChange={(e) => setActiveFilterType(e.target.value)}
                  className="px-4 py-3 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                >
                  {documentTypes.map(type => (
                    <option key={type} value={type} className="bg-deep-purple">
                      {type === 'all' ? 'All Types' : type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Documents List */}
          <div className="glass-dark p-6 overflow-hidden">
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-300">No documents found matching your criteria.</p>
              </div>
            ) : (
              <>
                {/* Table Header */}
                <div className="hidden md:grid grid-cols-12 gap-4 pb-4 border-b border-white border-opacity-10 text-gray-400 font-medium">
                  <div className="col-span-5">Name</div>
                  <div className="col-span-2">Type</div>
                  <div className="col-span-2">Modified</div>
                  <div className="col-span-2">Size</div>
                  <div className="col-span-1">Actions</div>
                </div>

                {/* Documents */}
                <div className="space-y-4 mt-4">
                  {filteredDocuments.map((doc, index) => (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center p-4 hover:bg-white hover:bg-opacity-5 rounded-lg transition-colors cursor-pointer"
                      onClick={() => setSelectedDocument(doc)}
                    >
                      <div className="col-span-5 flex items-center">
                        <div className="w-10 h-10 glass flex items-center justify-center rounded-lg mr-3">
                          {doc.type === 'PDF' && <span className="text-red-400">PDF</span>}
                          {doc.type === 'DOCX' && <span className="text-blue-400">DOC</span>}
                          {doc.type === 'XLSX' && <span className="text-green-400">XLS</span>}
                        </div>
                        <div>
                          <h3 className="text-white font-medium">{doc.title}</h3>
                          <p className="text-gray-400 text-sm">Owner: {doc.owner}</p>
                        </div>
                      </div>
                      <div className="col-span-2 text-gray-300 md:text-left text-sm">{doc.type}</div>
                      <div className="col-span-2 text-gray-300 md:text-left text-sm">{doc.lastModified}</div>
                      <div className="col-span-2 text-gray-300 md:text-left text-sm">{doc.size}</div>
                      <div className="col-span-1 flex justify-end">
                        <button className="p-2 glass rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                          </svg>
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Document Detail Modal */}
          {selectedDocument && (
            <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="glass max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
              >
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center">
                    <div className="w-12 h-12 glass flex items-center justify-center rounded-lg mr-4">
                      {selectedDocument.type === 'PDF' && <span className="text-red-400">PDF</span>}
                      {selectedDocument.type === 'DOCX' && <span className="text-blue-400">DOC</span>}
                      {selectedDocument.type === 'XLSX' && <span className="text-green-400">XLS</span>}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-white">{selectedDocument.title}</h2>
                      <p className="text-gray-300 mt-1">
                        {selectedDocument.type} • {selectedDocument.size} • Last modified: {selectedDocument.lastModified}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="text-gray-300 hover:text-white"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="mb-6">
                  <div className="flex flex-wrap gap-4 mb-4">
                    <span className="px-3 py-1 glass text-white text-sm rounded-full">
                      Owner: {selectedDocument.owner}
                    </span>
                    {selectedDocument.shared && (
                      <span className="px-3 py-1 bg-green-500 bg-opacity-20 text-green-300 text-sm rounded-full">
                        Shared
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="glass-dark p-6 mb-6 flex items-center justify-center h-64">
                  <p className="text-gray-300">Document preview would appear here</p>
                </div>
                
                <div className="mt-8 flex justify-end">
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="px-4 py-2 glass text-white rounded-lg mr-3 hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    className="px-4 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors mr-3"
                  >
                    Download
                  </button>
                  <button
                    className="px-4 py-2 glass text-white rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    Share
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

export default DocumentsPage 