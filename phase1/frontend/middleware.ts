import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Light, presence-only check: real token validation happens server-side
// on every API call. This just keeps unauthenticated users out of the UI.
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token');
  const isLoginPage = request.nextUrl.pathname.startsWith('/login');

  if (!token && !isLoginPage) return NextResponse.redirect(new URL('/login', request.url));
  if (token && isLoginPage) return NextResponse.redirect(new URL('/chat', request.url));
  return NextResponse.next();
}

export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] };
