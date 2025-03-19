import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { supabase } from '../lib/supabase'
import { User, AuthError } from '@supabase/supabase-js'

type AuthContextType = {
  user: User | null
  loading: boolean
  error: string | null
  signUp: (email: string, password: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  signInWithGoogle: () => Promise<void>
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Set up initial session
    const getSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        setUser(session?.user || null)
      } catch (error) {
        console.error('Error getting session:', error)
        setError('Failed to get user session')
      } finally {
        setLoading(false)
      }
    }

    getSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null)
      setLoading(false)
    })

    // Cleanup subscription on unmount
    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signUp = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)
      const { error } = await supabase.auth.signUp({ email, password })
      if (error) {
        throw error
      }
    } catch (error) {
      const authError = error as AuthError
      setError(authError.message || 'Error during sign up')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signIn = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) {
        throw error
      }
    } catch (error) {
      const authError = error as AuthError
      setError(authError.message || 'Error during sign in')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signInWithGoogle = async () => {
    try {
      setLoading(true)
      setError(null)
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/dashboard`
        }
      })
      if (error) {
        throw error
      }
    } catch (error) {
      const authError = error as AuthError
      setError(authError.message || 'Error signing in with Google')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    try {
      setLoading(true)
      setError(null)
      const { error } = await supabase.auth.signOut()
      if (error) {
        throw error
      }
    } catch (error) {
      const authError = error as AuthError
      setError(authError.message || 'Error during sign out')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        signUp,
        signIn,
        signOut,
        signInWithGoogle,
        clearError
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 