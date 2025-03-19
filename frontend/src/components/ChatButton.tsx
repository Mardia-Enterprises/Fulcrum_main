import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

const ChatButton = () => {
  const [isHovered, setIsHovered] = useState(false)
  const navigate = useNavigate()

  const handleChatClick = () => {
    navigate('/chat')
  }

  return (
    <motion.div 
      className="fixed bottom-10 right-10 z-50"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 0.5 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <button
        onClick={handleChatClick}
        className="w-20 h-20 rounded-full bg-bright-purple flex items-center justify-center shadow-2xl hover:bg-purple-600 transition-colors focus:outline-none"
        aria-label="Open Chat"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className="h-10 w-10 text-white" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
          strokeWidth={2}
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" 
          />
        </svg>
      </button>
      
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.8 }}
            className="absolute bottom-24 right-0 glass px-5 py-3 rounded-lg font-medium text-white text-lg whitespace-nowrap shadow-lg"
          >
            AI Assistant
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default ChatButton 