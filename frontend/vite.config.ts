import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from root directory
  const rootDir = path.resolve(process.cwd(), '..')
  const env = loadEnv(mode, rootDir, '')
  
  return {
    plugins: [react()],
    envDir: rootDir, // Set environment directory to root
    server: {
      watch: {
        usePolling: true,
      },
    },
    define: {
      // Make env variables available through import.meta.env
      'import.meta.env.VITE_SUPABASE_PROJECT_URL': JSON.stringify(env.VITE_SUPABASE_PROJECT_URL),
      'import.meta.env.VITE_SUPABASE_PUBLIC_API_KEY': JSON.stringify(env.VITE_SUPABASE_PUBLIC_API_KEY),
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
    },
  }
})
