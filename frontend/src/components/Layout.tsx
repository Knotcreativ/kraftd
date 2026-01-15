import React, { ReactNode } from 'react'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>KraftdIntel</h1>
          <p className="tagline">Intelligent Procurement Management</p>
        </div>
        <div className="navbar-menu">
          <a href="/dashboard" className="nav-link">Dashboard</a>
          <a href="/profile" className="nav-link">Profile</a>
          <a href="/logout" className="nav-link logout">Logout</a>
        </div>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
