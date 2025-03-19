import { useState, useEffect, ChangeEvent } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../lib/supabase'

interface Profile {
  id: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  organization: string;
  address: string;
  email: string;
  phone: string;
}

const ProfilePage = () => {
  const { user, signOut } = useAuth()
  const [profile, setProfile] = useState<Profile>({
    id: '',
    first_name: '',
    last_name: '',
    avatar_url: null,
    organization: '',
    address: '',
    email: '',
    phone: ''
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  
  useEffect(() => {
    if (user) {
      setProfile(prev => ({
        ...prev,
        id: user.id,
        email: user.email || '',
      }))
      
      fetchProfile()
    }
  }, [user])
  
  const fetchProfile = async () => {
    try {
      setLoading(true)
      
      if (!user) return
      
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single()
      
      if (error) {
        console.error('Error fetching profile:', error)
      } else if (data) {
        setProfile({
          id: user.id,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          avatar_url: data.avatar_url,
          organization: data.organization || '',
          address: data.address || '',
          email: user.email || '',
          phone: data.phone || ''
        })
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setProfile(prev => ({
      ...prev,
      [name]: value
    }))
  }
  
  const handleAvatarUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files.length) return
    
    try {
      setUploadingAvatar(true)
      
      const file = e.target.files[0]
      const fileExt = file.name.split('.').pop()
      const fileName = `${user?.id}-${Math.random().toString(36).substring(2)}.${fileExt}`
      const filePath = `avatars/${fileName}`
      
      const { error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(filePath, file)
      
      if (uploadError) {
        throw uploadError
      }
      
      const { data } = supabase.storage
        .from('avatars')
        .getPublicUrl(filePath)
      
      if (data) {
        setProfile(prev => ({
          ...prev,
          avatar_url: data.publicUrl
        }))
      }
    } catch (error) {
      console.error('Error uploading avatar:', error)
      setError('Error uploading avatar. Please try again.')
    } finally {
      setUploadingAvatar(false)
    }
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      setSaving(true)
      setError('')
      setSuccess('')
      
      if (!user) return
      
      const { error } = await supabase
        .from('profiles')
        .upsert({
          id: user.id,
          first_name: profile.first_name,
          last_name: profile.last_name,
          avatar_url: profile.avatar_url,
          organization: profile.organization,
          address: profile.address,
          phone: profile.phone,
          updated_at: new Date().toISOString()
        })
      
      if (error) {
        throw error
      }
      
      setSuccess('Profile updated successfully!')
    } catch (error) {
      console.error('Error updating profile:', error)
      setError('Error updating profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }
  
  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }
  
  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-white mb-6">Profile</h1>
          
          {loading ? (
            <div className="glass p-8 flex justify-center items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-bright-purple"></div>
            </div>
          ) : (
            <div className="glass p-6">
              {/* Profile Form */}
              <form onSubmit={handleSubmit}>
                {/* Avatar */}
                <div className="mb-6 flex flex-col items-center">
                  <div className="mb-4 relative">
                    <div className="w-32 h-32 rounded-full overflow-hidden glass flex items-center justify-center">
                      {profile.avatar_url ? (
                        <img 
                          src={profile.avatar_url} 
                          alt="Profile" 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-5xl text-white">
                          {profile.first_name && profile.first_name[0]}
                          {profile.last_name && profile.last_name[0]}
                        </span>
                      )}
                    </div>
                    <div className="absolute bottom-0 right-0">
                      <label className="cursor-pointer">
                        <div className="w-8 h-8 rounded-full bg-bright-purple flex items-center justify-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </div>
                        <input 
                          type="file" 
                          accept="image/*" 
                          className="hidden"
                          onChange={handleAvatarUpload}
                          disabled={uploadingAvatar}
                        />
                      </label>
                    </div>
                    {uploadingAvatar && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-full">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                      </div>
                    )}
                  </div>
                  <label className="text-white text-sm">
                    Edit Photo
                  </label>
                </div>
                
                {/* Alert Messages */}
                {error && (
                  <div className="mb-6 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-300">
                    {error}
                  </div>
                )}
                
                {success && (
                  <div className="mb-6 p-4 bg-green-500 bg-opacity-20 border border-green-500 rounded-lg text-green-300">
                    {success}
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* First Name */}
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-300 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={profile.first_name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                      required
                    />
                  </div>
                  
                  {/* Last Name */}
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-300 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={profile.last_name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                      required
                    />
                  </div>
                  
                  {/* Email */}
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={profile.email}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white bg-white bg-opacity-10 focus:outline-none"
                      disabled
                    />
                    <p className="mt-1 text-xs text-gray-400">Email cannot be changed</p>
                  </div>
                  
                  {/* Phone */}
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={profile.phone}
                      onChange={handleChange}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                    />
                  </div>
                  
                  {/* Organization */}
                  <div>
                    <label htmlFor="organization" className="block text-sm font-medium text-gray-300 mb-1">
                      Organization
                    </label>
                    <input
                      type="text"
                      id="organization"
                      name="organization"
                      value={profile.organization}
                      onChange={handleChange}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                    />
                  </div>
                  
                  {/* Address */}
                  <div>
                    <label htmlFor="address" className="block text-sm font-medium text-gray-300 mb-1">
                      Address
                    </label>
                    <input
                      type="text"
                      id="address"
                      name="address"
                      value={profile.address}
                      onChange={handleChange}
                      className="w-full px-4 py-2 glass border border-white border-opacity-20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-bright-purple"
                    />
                  </div>
                </div>
                
                <div className="mt-8 flex flex-col md:flex-row md:justify-between gap-4">
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="px-4 py-2 glass text-white rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    Sign Out
                  </button>
                  
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-6 py-2 bg-bright-purple text-white rounded-lg hover:bg-opacity-90 transition-colors disabled:opacity-70"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default ProfilePage 