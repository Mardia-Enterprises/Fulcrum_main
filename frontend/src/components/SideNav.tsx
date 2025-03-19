import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { motion, AnimatePresence } from 'framer-motion'

interface SideNavProps {
  isOpen: boolean;
  onClose: () => void;
}

const SideNav = ({ isOpen, onClose }: SideNavProps) => {
  const location = useLocation()
  const { user, signOut } = useAuth()

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/team', label: 'Team', icon: '👥' },
    { to: '/reports', label: 'Reports', icon: '📝' },
    { to: '/documents', label: 'Documents', icon: '📄' },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={onClose}
          />

          {/* Side Navigation */}
          <motion.div
            key="sidenav"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.3 }}
            className="fixed top-0 right-0 h-full w-64 glass-dark z-50 shadow-lg overflow-y-auto"
          >
            <div className="p-4 flex justify-end">
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-white hover:bg-opacity-10"
                aria-label="Close menu"
              >
                <svg className="w-6 h-6 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                  <path d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <div className="px-4 pb-6">
              <div className="flex items-center justify-center mb-8">
                <span className="text-white text-2xl font-bold flex items-center">
                  <span className="mr-2">⚡</span>
                  Engiverse
                </span>
              </div>

              <nav className="space-y-2">
                {navLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`flex items-center px-4 py-3 text-white rounded-lg transition-colors ${
                      location.pathname === link.to
                        ? 'bg-bright-purple bg-opacity-70'
                        : 'hover:bg-white hover:bg-opacity-10'
                    }`}
                    onClick={onClose}
                  >
                    <span className="mr-3 text-xl">{link.icon}</span>
                    <span>{link.label}</span>
                  </Link>
                ))}
              </nav>

              <div className="border-t border-white border-opacity-10 mt-8 pt-8">
                <Link
                  to="/profile"
                  className={`flex items-center px-4 py-3 text-white rounded-lg transition-colors ${
                    location.pathname === '/profile'
                      ? 'bg-bright-purple bg-opacity-70'
                      : 'hover:bg-white hover:bg-opacity-10'
                  }`}
                  onClick={onClose}
                >
                  <span className="mr-3 text-xl">👤</span>
                  <span>Profile</span>
                </Link>

                <button
                  onClick={() => {
                    signOut();
                    onClose();
                  }}
                  className="w-full flex items-center px-4 py-3 text-white rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors mt-2"
                >
                  <span className="mr-3 text-xl">🚪</span>
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default SideNav 