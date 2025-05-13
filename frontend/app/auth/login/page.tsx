'use client'

import { credentialLogin, githubSignIn, googleSignIn } from '@/lib/actions/auth'
import { motion } from 'framer-motion'
import { AuthError } from 'next-auth'
import { useSession } from 'next-auth/react'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { FaGithub, FaGoogle } from 'react-icons/fa'


interface FormData {
  email: string
  password: string
}

export default function LoginPage() {
  const { status, update } = useSession()
  const [error, setError] = useState<string | null>(null)


  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>()

  if (status === "loading") return null;
  if (status === "authenticated") return redirect("/dashboard");


  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await credentialLogin(data);
      await update();
      redirect("/dashboard")
    } catch (error) {
      if (error instanceof AuthError) {
        setError("Wrong email or password");
      } else {
        setError("Something went wrong, please try again")
      }
    }
  };

  return (
    <div className="relative flex min-h-screen bg-gradient-to-tr from-indigo-900 via-purple-900 to-pink-900 overflow-hidden pt-10">
      <nav className="fixed top-0 w-full z-50 bg-gray-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between p-4">
          <Link href="/" className="text-2xl font-black text-white">
            Data<span className="text-pink-400">Cube</span>
          </Link>
        </div>
      </nav>
      {/* Decorative rotating blobs */}
      <motion.div
        className="absolute top-[-20%] left-[-10%] w-[400px] h-[400px] bg-pink-500 rounded-full mix-blend-multiply opacity-30 filter blur-2xl"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 30, ease: 'linear' }}
      />
      <motion.div
        className="absolute bottom-[-25%] right-[-15%] w-[600px] h-[600px] bg-indigo-500 rounded-full mix-blend-screen opacity-30 filter blur-3xl"
        animate={{ rotate: -360 }}
        transition={{ repeat: Infinity, duration: 40, ease: 'linear' }}
      />

      <div className="relative z-10 flex flex-col md:flex-row flex-1 max-w-6xl mx-auto my-auto p-6 bg-white/5 rounded-3xl backdrop-blur-lg shadow-2xl overflow-hidden">
        {/* Left graphic / welcome */}
        <motion.div
          className="hidden md:flex flex-col justify-center flex-1 text-center px-8"
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-300 to-blue-500 mb-4">
            Welcome Back!
          </h2>
          <p className="text-gray-200">
            Log in to access your dashboards, APIs, and real‑time data
            analytics. New here?{' '}
            <Link href="/auth/register" className="text-green-300 hover:underline">
              Sign up
            </Link>
          </p>
          <motion.img
            src="/images/login-illustration.jpg"
            alt="Login illustration"
            className="mt-8 w-3/4 mx-auto"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.5 }}
          />
        </motion.div>

        {/* Right form */}
        <motion.div
          className="flex-1 px-6 py-8 md:py-12"
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-6 text-center">
            Sign In
          </h1>
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-6 max-w-md mx-auto"
          >
            <div>
              <label className="block text-sm text-gray-300 mb-1">Email</label>
              <input
                type="email"
                {...register('email', { required: 'Email required' })}
                className={`w-full px-4 py-2 rounded-lg bg-white/20 placeholder-gray-400 text-gray-100 focus:outline-none ${errors.email ? 'ring-2 ring-red-400' : 'ring-1 ring-white/30'
                  }`}
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1">Password</label>
              <input
                type="password"
                {...register('password', {
                  required: 'Password required',
                  minLength: { value: 6, message: 'At least 6 chars' },
                })}
                className={`w-full px-4 py-2 rounded-lg bg-white/20 placeholder-gray-400 text-gray-100 focus:outline-none ${errors.password
                  ? 'ring-2 ring-red-400'
                  : 'ring-1 ring-white/30'
                  }`}
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.password.message}
                </p>
              )}
            </div>

            {error && (
              <p className="mt-1 text-xs text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full flex justify-center items-center gap-2 py-3 rounded-full text-lg font-semibold ${isSubmitting
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-400 hover:bg-green-300'
                } transition`}
            >
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 max-w-md mx-auto space-y-4">
            <div className="flex items-center text-gray-400">
              <span className="flex-grow border-t border-gray-600" />
              <span className="px-3 text-sm">or continue with</span>
              <span className="flex-grow border-t border-gray-600" />
            </div>
            <div className="flex gap-4">
              <motion.button
                onClick={googleSignIn}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaGoogle className="text-red-500" size={20} /> Google
              </motion.button>
              <motion.button
                onClick={githubSignIn}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaGithub className="text-gray-200" size={20} /> GitHub
              </motion.button>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-gray-400">
            <Link href="/auth/forgot" className="hover:underline">
              Forgot password?
            </Link>{' '}
            |{' '}
            <Link href="/auth/register" className="hover:underline">
              Create an account
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
