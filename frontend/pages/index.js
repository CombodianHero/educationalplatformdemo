import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'

export default function Home() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [courses, setCourses] = useState([])
  const [fetchLoading, setFetchLoading] = useState(true)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchCourses()
    }
  }, [user])

  const fetchCourses = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/courses', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCourses(response.data)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    } finally {
      setFetchLoading(false)
    }
  }

  if (loading || fetchLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-400">
            MTProto Learning Platform
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-300">
              Welcome, {user?.username}
            </span>
            <button
              onClick={() => {
                localStorage.removeItem('access_token')
                router.push('/login')
              }}
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <h2 className="text-3xl font-bold mb-8">Available Courses</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div
              key={course.id}
              onClick={() => router.push(`/course/${course.id}`)}
              className="bg-gray-800 rounded-lg p-6 cursor-pointer hover:bg-gray-700 transition transform hover:scale-105"
            >
              <div className="h-40 bg-gray-700 rounded-lg mb-4 flex items-center justify-center">
                <span className="text-4xl">📚</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">{course.name}</h3>
              <p className="text-gray-400">
                {course.description || 'No description available'}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
