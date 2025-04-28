/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @next/next/no-img-element */
'use client'
import Loading from '@/components/Loading'
import { useDeleteAccount, useSettingsQuery, useUpdateSettings } from '@/hooks/useSettings'
import { motion } from 'framer-motion'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import {
    FaBell,
    FaCamera,
    FaLock,
    FaSlidersH,
    FaTrash,
    FaUser,
} from 'react-icons/fa'

const SectionCard: React.FC<{
    icon: React.ReactNode
    title: string
    children: React.ReactNode
}> = ({ icon, title, children }) => (
    <motion.div
        className="bg-gray-800 rounded-2xl shadow-2xl p-6"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
    >
        <div className="flex items-center mb-4">
            <div className="text-pink-400 text-2xl mr-3">{icon}</div>
            <h2 className="text-xl font-semibold">{title}</h2>
        </div>
        {children}
    </motion.div>
)

export default function SettingsPage() {
    const { data: session, status } = useSession()
    const user = session?.user

    const { data: settings, isLoading: loadingSettings } = useSettingsQuery()
    const updateSettings = useUpdateSettings()
    const deleteAccount = useDeleteAccount()

    const [emailNotif, setEmailNotif] = useState(true)
    const [pushNotif, setPushNotif] = useState(false)
    const [inAppNotif, setInAppNotif] = useState(true)
    const [theme, setTheme] = useState('Light')
    const [lang, setLang] = useState('English')

    // initialize local state when settings load
    useEffect(() => {
        if (settings) {
            setEmailNotif(settings.notifications?.email)
            setPushNotif(settings.notifications?.push)
            setInAppNotif(settings.notifications?.inApp)
            setTheme(settings.theme ? settings.theme : 'Dark')
            setLang(settings.language ? settings.language : 'English')
        }
    }, [settings])

    if (status === 'loading') return null;
    if (status === 'unauthenticated' || !user) {
        redirect("/auth/login")
    }
    if (loadingSettings) <Loading />

    const handleSave = () => {
        updateSettings.mutate(
            {
                notifications: {
                    email: emailNotif,
                    push: pushNotif,
                    inApp: inAppNotif,
                },
                theme,
                language: lang,
            },
            {
                onSuccess: () => alert('Settings saved!'),
                onError: (err: any) => alert('Save failed: ' + err.message),
            }
        )
    }

    const handleDelete = () => {
        if (!confirm('Delete your account? This action cannot be undone.')) return
        deleteAccount.mutate(undefined, {
            onError: (err: any) => alert('Delete failed: ' + err.message),
        })
    }

    return (
        <motion.div
            className="
        relative min-h-screen 
        bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 
        p-6 md:p-12 
        overflow-x-hidden
      "
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
        >
            <motion.div
                className="
          absolute -top-1/4 -right-1/4 
          w-[500px] h-[500px] 
          bg-pink-600 mix-blend-screen opacity-20 
          rounded-full filter blur-3xl
        "
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 50, ease: 'linear' }}
            />

            <div className="relative max-w-4xl mx-auto space-y-8">
                <motion.h1
                    className="
            text-4xl md:text-5xl font-extrabold 
            text-transparent bg-clip-text 
            bg-gradient-to-r from-pink-400 to-yellow-300 
            text-center mb-6
          "
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                >
                    Account Settings
                </motion.h1>

                <SectionCard icon={<FaUser />} title="Profile">
                    <div className="flex flex-col md:flex-row items-center md:items-start md:space-x-6">
                        <img
                            src={user.image || 'https://via.placeholder.com/150'}
                            alt="Avatar"
                            className="w-24 h-24 rounded-full object-cover mb-4 md:mb-0 shadow-lg"
                        />
                        <div className="flex-1 space-y-2">
                            <p className="text-lg font-medium">{user.name}</p>
                            <p className="text-gray-400">{user.email}</p>
                            <div className="flex flex-wrap gap-3 mt-4">
                                <button className="flex items-center gap-2 bg-pink-500 hover:bg-pink-400 text-gray-900 px-4 py-2 rounded-full transition">
                                    <FaCamera /> Change Photo
                                </button>
                                <button className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-full transition">
                                    Edit Profile
                                </button>
                                <button className="bg-yellow-600 hover:bg-yellow-500 px-4 py-2 rounded-full transition">
                                    Change Password
                                </button>
                            </div>
                        </div>
                    </div>
                </SectionCard>

                <SectionCard icon={<FaLock />} title="Security">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span>Two‑Factor Authentication</span>
                            <button className="bg-green-500 hover:bg-green-400 px-3 py-1 rounded-full text-sm transition">
                                Enable
                            </button>
                        </div>
                        <div className="flex justify-between items-center">
                            <span>Login History</span>
                            <button className="bg-blue-500 hover:bg-blue-400 px-3 py-1 rounded-full text-sm transition">
                                View
                            </button>
                        </div>
                    </div>
                </SectionCard>

                <SectionCard icon={<FaBell />} title="Notifications">
                    <div className="space-y-4">
                        {[
                            { label: 'Email Alerts', value: emailNotif, set: setEmailNotif },
                            { label: 'Push Notifications', value: pushNotif, set: setPushNotif },
                            { label: 'In‑App Messages', value: inAppNotif, set: setInAppNotif },
                        ].map((n) => (
                            <div key={n.label} className="flex justify-between items-center">
                                <span>{n.label}</span>
                                <input
                                    type="checkbox"
                                    checked={n.value}
                                    disabled={loadingSettings}
                                    onChange={(e) => n.set(e.target.checked)}
                                    className="w-6 h-6 text-pink-500 bg-gray-700 rounded transition"
                                />
                            </div>
                        ))}
                    </div>
                </SectionCard>

                <SectionCard icon={<FaSlidersH />} title="Appearance">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <div className="flex flex-col">
                            <label className="mb-2">Theme</label>
                            <select
                                value={theme}
                                disabled={loadingSettings}
                                onChange={(e) => setTheme(e.target.value)}
                                className="px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-pink-400"
                            >
                                <option>Light</option>
                                <option>Dark</option>
                                <option>System</option>
                            </select>
                        </div>
                        <div className="flex flex-col">
                            <label className="mb-2">Language</label>
                            <select
                                value={lang}
                                disabled={loadingSettings}
                                onChange={(e) => setLang(e.target.value)}
                                className="px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-pink-400"
                            >
                                <option>English</option>
                                <option>Spanish</option>
                                <option>French</option>
                            </select>
                        </div>
                    </div>
                </SectionCard>

                <SectionCard icon={<FaTrash />} title="Danger Zone">
                    <p className="text-red-400 mb-4">
                        Permanently delete your account and all data. This action cannot be undone.
                    </p>
                    <button
                        onClick={handleDelete}
                        disabled={deleteAccount.isPending}
                        className="bg-red-600 hover:bg-red-500 px-6 py-2 rounded-full font-semibold transition"
                    >
                        {deleteAccount.isPending ? 'Deleting...' : 'Delete My Account'}
                    </button>
                </SectionCard>

                <motion.div
                    className="text-right"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                >
                    <button
                        onClick={handleSave}
                        disabled={updateSettings.isPending || loadingSettings}
                        className="bg-green-500 hover:bg-green-400 px-8 py-3 rounded-full text-lg font-semibold transition shadow-lg"
                    >
                        {updateSettings.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                </motion.div>
            </div>
        </motion.div>
    )
}
