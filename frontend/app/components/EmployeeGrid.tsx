import { Employee } from '../services/api';

interface EmployeeGridProps {
  employees: Employee[];
  onSelectEmployee: (employee: Employee) => void;
  selectedEmployee: Employee | null;
}

export default function EmployeeGrid({ 
  employees, 
  onSelectEmployee, 
  selectedEmployee 
}: EmployeeGridProps) {
  // Function to generate a gradient background based on name
  const getInitialsBackground = (name: string) => {
    // Simple hash function to generate consistent colors
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Generate a hue value between 0 and 360
    const hue = hash % 360;
    
    // Use a high saturation and light value for vibrant but readable colors
    return `hsl(${hue}, 70%, 75%)`;
  };

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {employees.map((employee) => {
        const bgColor = getInitialsBackground(employee.name);
        const initials = employee.name.split(' ').map(name => name[0]).join('');
        
        return (
          <div
            key={employee.id || employee.name}
            className={`
              relative rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer
              ${selectedEmployee?.id === employee.id ? 'border-indigo-500 ring-2 ring-indigo-500' : 'border-gray-300'}
            `}
            onClick={() => onSelectEmployee(employee)}
          >
            <div className="flex flex-col items-center text-center">
              <div className="h-24 w-24 rounded-full overflow-hidden mb-4">
                {employee.imageUrl ? (
                  <img 
                    src={employee.imageUrl} 
                    alt={employee.name} 
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div 
                    className="flex h-full w-full items-center justify-center text-white"
                    style={{ backgroundColor: bgColor }}
                  >
                    <span className="text-2xl font-medium">{initials}</span>
                  </div>
                )}
              </div>
              <h3 className="text-lg font-medium text-gray-900">{employee.name}</h3>
              {employee.role && (
                <p className="text-sm text-gray-500">{employee.role}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
} 