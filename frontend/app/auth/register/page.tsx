/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import ErrorModal from '@/components/ErrorModal'
// import { githubSignIn, googleSignIn } from '@/lib/actions/auth'
import { motion } from 'framer-motion'
import { useSession } from 'next-auth/react'
import Link from 'next/link'
import { redirect, useRouter } from 'next/navigation'
import React from 'react'
import { useForm } from 'react-hook-form'
import { FaGithub, FaGoogle } from 'react-icons/fa'

interface RegisterData {
  email: string
  firstName: string
  lastName: string
  password: string
  confirmPassword?: string
}

export default function RegisterPage() {
  const { status } = useSession()
  const router = useRouter()



  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterData>()

  const [modalOpen, setModalOpen] = React.useState(false)
  const [modalMsg, setModalMsg] = React.useState('')

  if (status === "loading") return null;
  if (status === "authenticated") return redirect("/dashboard");

  const onSubmit = async (vals: RegisterData) => {
    const payload = { ...vals }
    delete payload.confirmPassword
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        router.push('/dashboard')
      } else {
        const body = await res.json()
        setModalMsg(body.error || 'Registration failed')
        setModalOpen(true)
      }
    } catch (err: unknown) {
      const errorMessage = (err instanceof Error && err.message) ? err.message : 'Network error';
      setModalMsg(errorMessage)
      setModalOpen(true)
    }
  }

  return (
    <div className="relative flex min-h-screen bg-gradient-to-tr from-purple-900 via-indigo-900 to-black overflow-hidden pt-11">
      <nav className="fixed top-0 w-full z-50 bg-gray-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between p-4">
          <Link href="/" className="text-2xl font-black text-white">
            Data<span className="text-pink-400">Cube</span>
          </Link>
        </div>
      </nav>
      {/* Background Blobs */}
      <motion.div
        className="absolute top-[-15%] left-[-10%] w-[500px] h-[500px] bg-pink-500 rounded-full mix-blend-multiply opacity-30 blur-3xl"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 40, ease: 'linear' }}
      />
      <motion.div
        className="absolute bottom-[-20%] right-[-15%] w-[600px] h-[600px] bg-green-500 rounded-full mix-blend-screen opacity-20 blur-2xl"
        animate={{ rotate: -360 }}
        transition={{ repeat: Infinity, duration: 50, ease: 'linear' }}
      />

      <ErrorModal
        isOpen={modalOpen}
        onRequestClose={() => setModalOpen(false)}
        errorMessage={modalMsg}
      />

      <div className="relative z-10 flex flex-col md:flex-row flex-1 max-w-6xl mx-auto my-auto bg-white/10 backdrop-blur-md rounded-3xl shadow-2xl overflow-hidden">
        {/* Left Panel */}
        <motion.div
          className="hidden md:flex flex-col justify-center flex-1 p-12 text-center"
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-300 to-blue-400 mb-4">
            Join the Future of Data
          </h2>
          <p className="text-gray-200 mb-6">
            Create your free account and get instant access to powerful APIs,
            real-time analytics, and seamless integrations.
          </p>
          <motion.img
            src="/images/register-illustration.jpg"
            alt="Register illustration"
            className="mx-auto w-3/4"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.5 }}
          />
        </motion.div>

        {/* Right Form */}
        <motion.div
          className="flex-1 p-8 md:p-12"
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-6 text-center">
            Create Account
          </h1>
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-5 max-w-md mx-auto"
          >
            {[
              { label: 'Email', name: 'email', type: 'email' },
              { label: 'First Name', name: 'firstName', type: 'text' },
              { label: 'Last Name', name: 'lastName', type: 'text' },
              { label: 'Password', name: 'password', type: 'password' },
              { label: 'Confirm Password', name: 'confirmPassword', type: 'password' },
            ].map((f) => (
              <div key={f.name}>
                <label className="block text-sm text-gray-300 mb-1">
                  {f.label}
                </label>
                <input
                  type={f.type}
                  {...register(f.name as any, {
                    required: `${f.label} is required`,
                    minLength:
                      f.name === 'password'
                        ? { value: 6, message: 'Min 6 characters' }
                        : undefined,
                    validate:
                      f.name === 'confirmPassword'
                        ? (v) => v === watch('password') || 'Passwords must match'
                        : undefined,
                  })}
                  className={`w-full px-4 py-2 rounded-lg bg-white/20 placeholder-gray-400 text-gray-100 focus:outline-none transition ${errors[f.name as keyof RegisterData]
                    ? 'ring-2 ring-red-400'
                    : 'ring-1 ring-white/30'
                    }`}
                  placeholder={
                    f.name === 'confirmPassword' ? '••••••••' : `Enter your ${f.label.toLowerCase()}`
                  }
                />
                {errors[f.name as keyof RegisterData] && (
                  <p className="mt-1 text-xs text-red-400">
                    {
                      (errors[f.name as keyof RegisterData]?.message as string) ||
                      'Error'
                    }
                  </p>
                )}
              </div>
            ))}

            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full flex justify-center items-center gap-2 py-3 rounded-full text-lg font-semibold ${isSubmitting
                ? 'bg-gray-500 cursor-not-allowed'
                : 'bg-green-400 hover:bg-green-300'
                } transition`}
            >
              {isSubmitting ? 'Creating…' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-8 max-w-md mx-auto">
            <div className="flex items-center text-gray-400 mb-4">
              <span className="flex-grow border-t border-gray-600" />
              <span className="px-3 text-sm">or sign up with</span>
              <span className="flex-grow border-t border-gray-600" />
            </div>
            <div className="flex gap-4">
              <motion.button
                disabled
                onClick={() => { }}
                // onClick={googleSignIn}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaGoogle className="text-red-500" size={20} /> Google
              </motion.button>
              <motion.button
                disabled
                onClick={() => { }}
                // onClick={githubSignIn}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaGithub className="text-gray-200" size={20} /> GitHub
              </motion.button>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-gray-300">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-green-300 hover:underline">
              Log In
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
