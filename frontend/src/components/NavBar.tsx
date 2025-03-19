import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { motion } from 'framer-motion'
import SideNav from './SideNav'

const NavBar = () => {
  const [isSideNavOpen, setIsSideNavOpen] = useState(false)
  const { user } = useAuth()

  return (
    <>
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

          {/* Hamburger Menu Button */}
          <button
            onClick={() => setIsSideNavOpen(true)}
            className="glass p-2 rounded-lg focus:outline-none"
            aria-label="Open menu"
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
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </nav>

      {/* Side Navigation */}
      <SideNav isOpen={isSideNavOpen} onClose={() => setIsSideNavOpen(false)} />
    </>
  )
}

export default NavBar 