export default function Home() {
  return (
    <main className="py-10 lg:pl-72">
      <div className="px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Fulcrum Dashboard</h1>
        <div className="bg-white shadow-md rounded-lg p-6">
          <p className="text-gray-700 mb-4">
            Welcome to the Fulcrum application. Use the sidebar navigation or the links below to explore.
          </p>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="/teams" 
              className="block p-4 bg-indigo-600 text-white text-center rounded-md hover:bg-indigo-700 transition-colors"
            >
              View Team Members
            </a>
            <a 
              href="#" 
              className="block p-4 bg-gray-200 text-gray-800 text-center rounded-md hover:bg-gray-300 transition-colors"
            >
              View Projects
            </a>
          </div>
        </div>
      </div>
    </main>
  );
} 