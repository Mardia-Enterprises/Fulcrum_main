import { Employee, EmployeeDetails as ApiEmployeeDetails } from '../services/api';

interface EmployeeDetailsProps {
  employee: Employee;
  details: ApiEmployeeDetails | null;
  loading: boolean;
  onClose: () => void;
}

interface Project {
  title_and_location?: string[] | string;
  scope?: string;
  role?: string[] | string;
  fee?: string;
  cost?: string;
}

export default function EmployeeDetails({ 
  employee, 
  details, 
  loading,
  onClose 
}: EmployeeDetailsProps) {
  if (!employee) return null;

  const renderProjects = (projects: any[]) => {
    return projects.map((project: Project, index: number) => (
      <div key={index} className="bg-white p-4 rounded-md shadow-sm mb-4 border border-gray-100">
        <h5 className="font-medium text-gray-900 mb-2">
          {Array.isArray(project.title_and_location) 
            ? project.title_and_location[0] 
            : (project.title_and_location || 'Unnamed Project')}
        </h5>
        
        {Array.isArray(project.title_and_location) && project.title_and_location[1] && (
          <p className="text-sm text-gray-500 mb-2">{project.title_and_location[1]}</p>
        )}
        
        {project.scope && (
          <div className="mt-2">
            <p className="text-sm text-gray-800">{project.scope}</p>
          </div>
        )}
        
        <div className="mt-3 flex flex-wrap gap-2">
          {project.role && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              {Array.isArray(project.role) ? project.role.join(', ') : project.role}
            </span>
          )}
          
          {project.fee && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Fee: {project.fee}
            </span>
          )}
          
          {project.cost && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Cost: {project.cost}
            </span>
          )}
        </div>
      </div>
    ));
  };

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden border border-gray-200">
      <div className="flex justify-between items-center border-b border-gray-200 p-4 bg-gray-50">
        <h2 className="text-xl font-semibold text-gray-800">Employee Details</h2>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M6 18L18 6M6 6l12 12" 
            />
          </svg>
        </button>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-10">
            <p className="text-gray-500">Loading details...</p>
          </div>
        ) : (
          <div>
            <div className="flex flex-col sm:flex-row items-center sm:items-start mb-6">
              <div className="h-32 w-32 rounded-full overflow-hidden bg-gray-100 mb-4 sm:mb-0 sm:mr-6 flex-shrink-0">
                {employee.imageUrl ? (
                  <img 
                    src={employee.imageUrl} 
                    alt={employee.name} 
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-indigo-100 text-indigo-700">
                    <span className="text-3xl font-medium">
                      {employee.name.split(' ').map(name => name[0]).join('')}
                    </span>
                  </div>
                )}
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-1">{employee.name}</h3>
                <p className="text-lg text-indigo-600 mb-2">{details?.role || employee.role || 'Employee'}</p>
                {details?.education && (
                  <p className="text-gray-600 text-sm mb-2">
                    {details.education}
                  </p>
                )}
                {details?.years_experience && (
                  <p className="text-gray-600 text-sm">
                    Experience: {details.years_experience} years
                  </p>
                )}
                {employee.email && (
                  <p className="text-gray-500 flex items-center mt-2">
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className="h-5 w-5 mr-2" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" 
                      />
                    </svg>
                    {employee.email}
                  </p>
                )}
              </div>
            </div>

            {details && (
              <div className="mt-6">
                {details.relevant_projects && details.relevant_projects.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Relevant Projects</h4>
                    <div className="space-y-4">
                      {renderProjects(details.relevant_projects)}
                    </div>
                  </div>
                )}
                
                {details.resume_data && Object.keys(details.resume_data).length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Additional Information</h4>
                    <div className="bg-gray-50 rounded-md p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(details.resume_data)
                        .filter(([key]) => !['Role', 'relevant_projects'].includes(key)) // Skip fields we're already displaying
                        .map(([key, value]) => (
                          <div key={key} className="mb-2">
                            <h5 className="text-sm font-medium text-gray-500">{key}</h5>
                            <p className="text-gray-800">
                              {typeof value === 'string' ? value : JSON.stringify(value)}
                            </p>
                          </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 