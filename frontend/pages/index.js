import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'

export default function Home() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [courses, setCourses] = useState([])

  useEffect(() => {
    if (!loading && !user) router.push('/login')
  }, [user, loading])

  useEffect(() => {
    if (user) axios.get('/api/courses', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
      .then(r => setCourses(r.data))
  }, [user])

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-10 w-10 border-4 border-blue-500 rounded-full border-t-transparent"></div></div>

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 p-4 flex justify-between">
        <h1 className="text-2xl font-bold text-blue-400">📚 MTProto Learning</h1>
        <div className="flex gap-4 items-center">
          <span>{user?.username} ({user?.role})</span>
          <button onClick={() => { logout(); router.push('/login') }} className="bg-red-600 px-4 py-2 rounded">Logout</button>
        </div>
      </header>
      <main className="p-8">
        <h2 className="text-3xl mb-6">Courses</h2>
        <div className="grid grid-cols-3 gap-6">
          {courses.map(c => (
            <div key={c.id} className="bg-gray-800 p-6 rounded cursor-pointer hover:bg-gray-700" onClick={() => router.push(`/course/${c.id}`)}>
              <h3 className="text-xl">{c.name}</h3>
              <p className="text-gray-400">{c.description}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
