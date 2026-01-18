import React, { ReactNode } from 'react'
import { useAuth } from '../context/AuthContext'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>KraftdIntel</h1>
          <p className="tagline">Intelligent Procurement Management</p>
        </div>
        <div className="navbar-menu">
          <a href="/dashboard" className="nav-link">Dashboard</a>
          <a href="/streaming-dashboard" className="nav-link">Real-Time</a>
          <a href="/analytics" className="nav-link">Analytics</a>
          <a href="/dashboard-builder" className="nav-link">Custom Dashboard</a>
          <a href="/profile" className="nav-link">Profile</a>
          <button className="nav-link logout" onClick={handleLogout}>Logout</button>
        </div>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
