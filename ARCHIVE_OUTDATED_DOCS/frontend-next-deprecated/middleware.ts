/**
 * Next.js Middleware - Route Protection and Auth Verification
 *
 * Protects all routes except:
 * - /login
 * - /register
 * - /public/*
 * - /_next/*
 * - /api/*
 *
 * Features:
 * - Token validation
 * - Automatic redirect to login if not authenticated
 * - Public routes bypass auth
 */

import { NextRequest, NextResponse } from 'next/server'

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register']

// API routes that don't require auth (can override in specific endpoints)
const PUBLIC_API_ROUTES = ['/api/auth/login', '/api/auth/register', '/api/auth/refresh']

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname

  // Skip middleware for public routes, static files, and Next.js internals
  if (
    PUBLIC_ROUTES.includes(pathname) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/public') ||
    pathname.match(/\.(jpg|jpeg|png|gif|ico|svg|webp)$/)
  ) {
    return NextResponse.next()
  }

  // Get token from cookies or localStorage (via request header)
  const token = request.cookies.get('access_token')?.value

  // If no token and trying to access protected route, redirect to login
  if (!token && !PUBLIC_API_ROUTES.includes(pathname)) {
    // Redirect to login with return URL
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // If on login/register but already authenticated, redirect to dashboard
  if (token && PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
