// app/features/page.tsx
'use client'
import React from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
    FaCube,
    FaChartLine,
    FaLock,
    FaBook,
    FaPlug,
    FaBolt,
    FaCogs,
    FaMobileAlt,
} from 'react-icons/fa'
import Image from 'next/image';
import { Navbar } from '@/components/NavBar'
import { Footer } from '@/components/Footer'

const features = [
    {
        icon: <FaCube size={48} className="text-pink-400" />,
        title: 'Schema‑less Storage',
        desc: 'Store any JSON shape without migrations or downtime. Model on the fly.',
    },
    {
        icon: <FaChartLine size={48} className="text-green-400" />,
        title: 'Real‑Time Analytics',
        desc: 'Built‑in dashboards and streaming webhooks keep you ahead of the curve.',
    },
    {
        icon: <FaLock size={48} className="text-blue-400" />,
        title: 'Enterprise Security',
        desc: 'End‑to‑end encryption, SOC2 compliance, RBAC and SSO support.',
    },
    {
        icon: <FaBook size={48} className="text-yellow-400" />,
        title: 'Interactive Docs',
        desc: 'Live Try‑It‑Now console, code samples in 10+ languages, and tutorials.',
    },
    {
        icon: <FaPlug size={48} className="text-purple-400" />,
        title: 'Seamless SDKs',
        desc: 'Official SDKs for JavaScript, Python, Go, Java, and more—always up to date.',
    },
    {
        icon: <FaBolt size={48} className="text-red-400" />,
        title: 'Blazing Fast',
        desc: 'Sub‑10ms reads, sub‑20ms writes at any scale with global replication.',
    },
    {
        icon: <FaCogs size={48} className="text-indigo-400" />,
        title: 'Full‑Stack Integrations',
        desc: 'Next.js, React Native, Serverless, GraphQL — pick your stack.',
    },
    {
        icon: <FaMobileAlt size={48} className="text-teal-400" />,
        title: 'Mobile Ready',
        desc: 'Offline mode, delta sync, and live queries for flutter & React Native apps.',
    },
]

export default function FeaturesPage() {
    return (
        <div className="font-sans text-gray-100 bg-gray-900">
            {/* Navbar */}
            <Navbar />

            {/* Background blobs */}
            {/* Hero */}
            <section
                className="relative flex items-center justify-center text-center h-96 bg-cover bg-center"
                style={{ backgroundImage: "url('/images/features-hero.jpg')" }}
            >
                <div className="absolute inset-0 bg-black/60" />
                <motion.div
                    className="relative z-10 px-6"
                    initial={{ y: 30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ duration: 0.8 }}
                >
                    <h1 className="text-4xl md:text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 to-yellow-300 mb-4">
                        Our Platform Features
                    </h1>
                    <p className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto">
                        Discover the powerful building blocks that make DataCube the most
                        flexible, secure, and scalable data platform for modern apps.
                    </p>
                </motion.div>
                {/* Animated blob */}
                <motion.div
                    className="absolute top-10 left-1/4 w-80 h-80 bg-gradient-to-tr from-pink-500 to-yellow-400 rounded-full mix-blend-screen opacity-70 filter blur-2xl"
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 25, ease: 'linear' }}
                />
            </section>

            {/* Masonry Grid */}
            <section className="py-20">
                <div className="max-w-6xl mx-auto px-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-fr">
                        {features.map((f, i) => {
                            // enlarge alternate cards for a dynamic layout
                            const span =
                                i % 5 === 0
                                    ? 'md:col-span-2 md:row-span-2'
                                    : i % 4 === 3
                                        ? 'md:col-span-2'
                                        : ''
                            return (
                                <motion.div
                                    key={i}
                                    className={`${span} bg-gray-800 p-8 rounded-3xl shadow-2xl flex flex-col justify-between`}
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    whileInView={{ scale: 1, opacity: 1 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.2 }}
                                >
                                    <div className="mb-6">{f.icon}</div>
                                    <h3 className="text-2xl font-bold mb-2">{f.title}</h3>
                                    <p className="text-gray-400 flex-grow">{f.desc}</p>
                                    <Link
                                        href={`/features#${f.title.replace(/\s+/g, '-').toLowerCase()}`}
                                        className="mt-6 inline-flex items-center text-pink-400 hover:underline"
                                    >
                                        Explore&nbsp;Feature →
                                    </Link>
                                </motion.div>
                            )
                        })}
                    </div>
                </div>
            </section>

            {/* Detailed Sections */}
            <section className="bg-gray-800 py-20 space-y-20">
                {features.map((f, i) => (
                    <motion.div
                        id={f.title.replace(/\s+/g, '-').toLowerCase()}
                        key={i}
                        className={`max-w-5xl mx-auto flex flex-col ${i % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
                            } items-center gap-12 px-4`}
                        initial={{ opacity: 0, x: i % 2 === 0 ? -50 : 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                    >
                        <div className="flex-1 space-y-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-pink-600 rounded-full">{f.icon}</div>
                                <h2 className="text-3xl font-bold">{f.title}</h2>
                            </div>
                            <p className="text-gray-300 leading-relaxed">{f.desc}</p>
                            <Link
                                href="/docs"
                                className="inline-block px-6 py-3 bg-pink-400 rounded-full text-gray-900 font-semibold hover:bg-pink-300 transition"
                            >
                                Read Docs
                            </Link>
                        </div>
                        {/* Placeholder illustration */}
                        <div className="flex-1">


                            <Image
                                src={`/images/feature-${i + 1}.svg`}
                                alt={f.title}
                                width={500}
                                height={500}
                                className="w-full h-auto"
                            />
                        </div>
                    </motion.div>
                ))}
            </section>

            {/* Call to Action */}
            <section className="py-16 bg-gradient-to-r from-pink-500 to-yellow-400">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <motion.h2
                        className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4"
                        initial={{ scale: 0.8, opacity: 0 }}
                        whileInView={{ scale: 1, opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        Ready to Build with DataCube?
                    </motion.h2>
                    <Link
                        href="/auth/register"
                        className="inline-block px-10 py-4 bg-gray-900 text-white font-semibold rounded-full hover:bg-gray-800 transition"
                    >
                        Start Your Free Trial
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <Footer />

            {/* Background blobs */}
        </div>
    )
}