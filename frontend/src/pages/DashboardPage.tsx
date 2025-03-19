import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { API_URL } from '../lib/supabase'
import ChatButton from '../components/ChatButton'

interface Engineer {
  id: string
  name: string
  role: string
  experience: number
  education: string
  skills: string[]
  projects: string[]
}

interface ChartData {
  id: string;
  title: string;
  data: number[];
  labels: string[];
  type: 'line' | 'bar';
  color: string;
}

const DashboardPage = () => {
  const { user } = useAuth()
  const [userName, setUserName] = useState('User')
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState<{
    charts: ChartData[];
    stats: { label: string; value: string | number; change: number }[];
  }>({
    charts: [],
    stats: []
  })

  useEffect(() => {
    // Get user's name when component mounts
    if (user?.user_metadata?.full_name) {
      setUserName(user.user_metadata.full_name)
    } else if (user?.email) {
      // Use email as fallback
      const emailName = user.email.split('@')[0]
      setUserName(emailName.charAt(0).toUpperCase() + emailName.slice(1))
    }

    // Mock dashboard data
    setTimeout(() => {
      setDashboardData({
        charts: [
          {
            id: 'chart1',
            title: 'Employee Engagement',
            type: 'line',
            data: [65, 72, 86, 81, 90, 87, 94],
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            color: '#8B5CF6'
          },
          {
            id: 'chart2',
            title: 'Project Progress',
            type: 'bar',
            data: [70, 45, 80, 30, 95, 60],
            labels: ['Project A', 'Project B', 'Project C', 'Project D', 'Project E', 'Project F'],
            color: '#3B82F6'
          }
        ],
        stats: [
          { label: 'Total Employees', value: 287, change: 12 },
          { label: 'Active Projects', value: 24, change: 3 },
          { label: 'Average Satisfaction', value: '92%', change: 5 },
          { label: 'Tasks Completed', value: 1432, change: 8 }
        ]
      })
      setLoading(false)
    }, 1000)
  }, [user])

  // Simple implementation to render chart-like components
  const renderChart = (chart: ChartData) => {
    if (chart.type === 'line') {
      return (
        <div className="h-40 flex items-end space-x-2">
          {chart.data.map((value, index) => (
            <div 
              key={index} 
              className="relative flex-1 flex items-end"
            >
              <div
                className="w-full bg-opacity-50 rounded-t"
                style={{ 
                  height: `${value}%`, 
                  backgroundColor: chart.color,
                  maxHeight: '100%'
                }}
              />
              {index < chart.data.length - 1 && (
                <div 
                  className="absolute right-0 top-0 h-px w-full transform translate-y-0" 
                  style={{ 
                    backgroundColor: chart.color,
                    transform: `rotate(${Math.atan2(
                      chart.data[index + 1] - value, 
                      10
                    )}rad)`,
                    transformOrigin: 'right bottom',
                    width: '100%'
                  }}
                />
              )}
              <div className="text-xs text-gray-400 mt-2">{chart.labels[index]}</div>
            </div>
          ))}
        </div>
      )
    }
    
    return (
      <div className="h-40 flex items-end space-x-2">
        {chart.data.map((value, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div 
              className="w-full rounded-t transition-all"
              style={{ 
                height: `${value}%`, 
                backgroundColor: chart.color,
                maxHeight: '100%'
              }}
            />
            <div className="text-xs text-gray-400 mt-2 truncate max-w-full">{chart.labels[index]}</div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="glass p-6 mb-6">
            <h1 className="text-3xl font-bold text-white">
              Welcome back, <span className="text-bright-purple">{userName}</span>
            </h1>
            <p className="text-gray-300 mt-2">
              Here's an overview of your team's performance
            </p>
          </div>

          {loading ? (
            <div className="glass-dark p-8 flex justify-center items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-bright-purple"></div>
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                {dashboardData.stats.map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    className="glass p-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <div className="text-gray-400 text-sm mb-1">{stat.label}</div>
                    <div className="text-white text-2xl font-bold">{stat.value}</div>
                    <div className={`text-sm mt-2 ${stat.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stat.change >= 0 ? '↑' : '↓'} {Math.abs(stat.change)}% from last month
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {dashboardData.charts.map((chart, index) => (
                  <motion.div
                    key={chart.id}
                    className="glass-dark p-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
                  >
                    <h3 className="text-white text-lg font-medium mb-4">{chart.title}</h3>
                    {renderChart(chart)}
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </div>
      
      <ChatButton />
    </div>
  )
}

export default DashboardPage 