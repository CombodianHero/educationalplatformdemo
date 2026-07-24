import { useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async e => {
    e.preventDefault()
    try {
      await login(username, password)
      router.push('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-gray-800 p-8 rounded-lg w-96">
        <h1 className="text-2xl font-bold mb-6 text-blue-400">Login</h1>
        {error && <div className="bg-red-600 text-white p-2 rounded mb-4">{error}</div>}
        <input className="w-full p-2 mb-4 bg-gray-700 rounded" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" className="w-full p-2 mb-4 bg-gray-700 rounded" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="w-full bg-blue-600 p-2 rounded hover:bg-blue-700">Login</button>
        <p className="text-gray-400 mt-4 text-sm">Demo: admin/admin123 or student/student123</p>
      </form>
    </div>
  )
}
