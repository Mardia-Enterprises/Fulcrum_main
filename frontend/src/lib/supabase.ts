import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Load environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_PROJECT_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLIC_API_KEY
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables. Check your .env file at project root.')
}

// Create Supabase client
export const supabase: SupabaseClient = createClient(
  supabaseUrl as string,
  supabaseAnonKey as string
)

// Helper functions for auth
export const getSession = async () => {
  return await supabase.auth.getSession()
}

export const getCurrentUser = async () => {
  return await supabase.auth.getUser()
}

export const signOut = async () => {
  return await supabase.auth.signOut()
}

// Function to check if a user is authenticated
export const isAuthenticated = async (): Promise<boolean> => {
  const { data } = await getSession()
  return !!data.session
}

// Function to get user data from a table if needed
export const getUserData = async (userId: string) => {
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

  if (error) {
    console.error('Error fetching user data:', error)
    return null
  }

  return data
}

export default supabase 