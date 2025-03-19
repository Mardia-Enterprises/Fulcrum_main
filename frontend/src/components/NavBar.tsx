import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { motion } from 'framer-motion'

const NavBar = () => {
  const location = useLocation()
  const { user, signOut } = useAuth()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  return (
    <nav className="glass-nav py-4 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo */}
        <Link to="/" className="flex items-center">
          <span className="text-white text-2xl font-bold flex items-center">
            <motion.span
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: 0 }}
              className="mr-2 inline-block"
            >
              ⚡
            </motion.span>
            Engiverse
          </span>
        </Link>

        {/* Mobile Menu Button */}
        <button
          onClick={toggleMenu}
          className="glass p-2 rounded-lg focus:outline-none"
          aria-label="Toggle menu"
        >
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            {isMenuOpen ? (
              <path d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3 }}
          className="mt-4 glass p-4 rounded-lg"
        >
          <div className="flex flex-col space-y-4">
            <Link 
              to="/" 
              className={`text-white hover:text-gray-300 transition-colors ${location.pathname === '/' ? 'font-medium' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className={`text-white hover:text-gray-300 transition-colors ${location.pathname === '/about' ? 'font-medium' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              About
            </Link>
            <Link 
              to="/contact" 
              className={`text-white hover:text-gray-300 transition-colors ${location.pathname === '/contact' ? 'font-medium' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </Link>
            
            {user ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="btn btn-outline w-full text-center"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <button 
                  onClick={() => {
                    handleSignOut()
                    setIsMenuOpen(false)
                  }}
                  className="text-white hover:text-gray-300 transition-colors"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link 
                  to="/login" 
                  className="btn btn-outline w-full text-center"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Login
                </Link>
                <Link 
                  to="/signup" 
                  className="btn btn-primary w-full text-center"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </motion.div>
      )}
    </nav>
  )
}

export default NavBar 