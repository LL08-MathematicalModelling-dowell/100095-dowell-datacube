/* eslint-disable @next/next/no-img-element */

'use client'
import React from 'react'
import Link from 'next/link'
import { useSession, } from 'next-auth/react'
import { motion } from 'framer-motion'
import {
  FaCube,
  FaChartLine,
  FaLock,
  FaBook,
  FaGithub,
  FaTwitter,
  FaLinkedin,
} from 'react-icons/fa'
import { Navbar } from '@/components/NavBar'


export default function Home() {
  const { data: session } = useSession()
  const isAuth = !!session

  const features = [
    {
      icon: <FaCube size={48} className="text-pink-400" />,
      title: 'Modular Storage',
      desc: 'Arbitrary JSON shapes, schemaless but indexed for fast queries.',
    },
    {
      icon: <FaChartLine size={48} className="text-green-400" />,
      title: 'Live Analytics',
      desc: 'Dashboards & webhooks update in real‑time so you never miss a beat.',
    },
    {
      icon: <FaLock size={48} className="text-blue-400" />,
      title: 'Zero‑Trust Security',
      desc: 'End‑to‑end encryption, SOC2‑compliant, role‑based access control.',
    },
    {
      icon: <FaBook size={48} className="text-yellow-400" />,
      title: 'Dev‑Focused Docs',
      desc: 'Interactive tutorials, one‑click code samples, and SDKs for all languages.',
    },
  ]

  return (
    <div className="relative font-sans text-gray-100 bg-gray-900 overflow-x-hidden pt-20">
      {/* Navbar */}
      <Navbar />
      {/* Hero */}
      <header className="relative h-screen pt-20 flex items-center justify-center text-center px-4">
        {/* background image */}
        <div className="absolute inset-0">
          <img
            src="/images/hero-bg.jpg"
            alt="Background"
            className="w-full h-full object-cover opacity-30"
          />
          {/* rotating gradient blob */}
          <motion.div
            className="absolute top-1/4 left-1/3 w-96 h-96 bg-gradient-to-tr from-pink-500 to-yellow-400 rounded-full mix-blend-screen opacity-70"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
          />
        </div>
        <motion.div
          className="relative max-w-2xl"
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-pink-400 to-yellow-300">
            Reimagine Your Data Workflows
          </h1>
          <p className="text-lg sm:text-xl mb-8 text-gray-300">
            A blazing‑fast, infinitely scalable API platform for modern
            applications—no schema, no limits.
          </p>
          {!isAuth && (
            <div className="flex justify-center gap-4">
              <Link
                href="/auth/register"
                className="px-8 py-3 bg-pink-400 rounded-full text-gray-900 font-semibold hover:bg-pink-300 transition"
              >
                Get Started
              </Link>
              <Link
                href="/auth/login"
                className="px-8 py-3 border-2 border-pink-400 rounded-full font-semibold hover:bg-pink-400 hover:text-gray-900 transition"
              >
                Log In
              </Link>
            </div>
          )}
        </motion.div>
      </header>

      {/* Features Masonry Grid */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            Key Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-fr">
            {features.map((f, i) => {
              // make first big, others smaller
              const colSpan = i === 0 ? 'md:col-span-2 md:row-span-2' : ''
              return (
                <motion.div
                  key={i}
                  className={`${colSpan} bg-gray-800 rounded-2xl p-8 flex flex-col justify-between shadow-2xl`}
                  initial={{ scale: 0.9, opacity: 0 }}
                  whileInView={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.2 * i }}
                >
                  <div className="mb-6">{f.icon}</div>
                  <h3 className="text-2xl font-semibold mb-2">{f.title}</h3>
                  <p className="text-gray-400 flex-grow">{f.desc}</p>
                  <Link
                    href="/features"
                    className="mt-6 inline-flex items-center text-pink-400 hover:underline"
                  >
                    Learn More →
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Live Stats */}
      <section className="py-20 bg-gradient-to-b from-gray-800 to-gray-900">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          {[
            { label: 'Databases', value: '1542+' },
            { label: 'Collections', value: '12 837+' },
            { label: 'API Requests/Day', value: '1M+' },
          ].map((s, i) => (
            <motion.div
              key={i}
              className="bg-gray-800 p-8 rounded-2xl shadow-lg"
              initial={{ y: 30, opacity: 0 }}
              whileInView={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 * i }}
            >
              <p className="text-5xl font-extrabold text-pink-400 mb-2">
                {s.value}
              </p>
              <p className="uppercase text-gray-400">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-16 bg-pink-500">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.h2
            className="text-3xl md:text-4xl font-bold text-white mb-4"
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
          >
            Ready to Focus on Your Product, Not Your Database?
          </motion.h2>
          <Link
            href={isAuth ? '/dashboard' : '/auth/register'}
            className="inline-block px-10 py-4 bg-gray-900 text-white font-semibold rounded-full hover:bg-gray-800 transition"
          >
            {isAuth ? 'Go to Dashboard' : 'Start Free Trial'}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between">
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} DataCube Inc. All rights reserved.
          </p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            {[FaGithub, FaTwitter, FaLinkedin].map((Icon, i) => (
              <Icon
                key={i}
                size={20}
                className="text-gray-500 hover:text-pink-400 transition"
              />
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}




