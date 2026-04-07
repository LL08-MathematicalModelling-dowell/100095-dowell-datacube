import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'

// extract navbar and footer to separate components
export const Navbar = () => {
  const { data: session } = useSession()
  const isAuth = !!session
  const initials = session?.user?.name
    ?.split(' ')
    .map((w) => w[0])
    .join('') || ''

  return (
    <nav className="fixed top-0 w-full z-50 bg-gray-900/80 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between p-4">
        <Link href="/" className="text-2xl font-black text-white">
          Data<span className="text-pink-400">Cube</span>
        </Link>
        <div className="flex items-center space-x-4">
          {isAuth ? (
            <>
              <div className="w-8 h-8 bg-pink-400 rounded-full flex items-center justify-center font-semibold text-gray-900">
                {initials}
              </div>
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-pink-400 rounded-lg text-gray-900 hover:bg-pink-300 transition"
              >
                Dashboard
              </Link>
              <button
                onClick={() => signOut()}
                className="px-4 py-2 bg-red-600 rounded-lg hover:bg-red-500 transition"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/auth/register"
                className="px-4 py-2 bg-pink-400 rounded-lg text-gray-900 hover:bg-pink-300 transition"
              >
                Sign Up
              </Link>
              <Link
                href="/auth/login"
                className="px-4 py-2 border border-pink-400 rounded-lg hover:bg-pink-400 transition"
              >
                Log In
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
