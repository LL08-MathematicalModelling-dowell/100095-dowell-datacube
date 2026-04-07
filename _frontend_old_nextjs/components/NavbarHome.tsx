// components/Navbar.tsx
'use client';
import React from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
// import Avatar from 'react-avatar';

const Navbar: React.FC = () => {
    const { data: session } = useSession();

    return (
        <nav className="bg-gray-900 text-white p-4">
            <div className="container mx-auto flex justify-between items-center">
                <Link href="/" className="text-xl font-bold text-orange-400">API Service</Link>
                <div className="flex items-center space-x-4">
                    {session ? (
                        <>
                            <Link href="/dashboard" className="hover:text-orange-400">Dashboard</Link>
                            <button
                                onClick={() => signOut()}
                                className="hover:text-orange-400"
                            >
                                Logout
                            </button>
                            <div className="flex items-center space-x-2">
                                {/* <Avatar
                                    name={session.user?.name || 'User'}
                                    size="40"
                                    round={true}
                                    className="border-2 border-orange-500"
                                /> */}
                                <span className="text-orange-400">👋</span>
                                <span>{session.user?.name || 'User'}</span>
                            </div>
                        </>
                    ) : (
                        <>
                            <Link href="/auth/login" className="hover:text-orange-400">Login</Link>
                            <Link href="/auth/register" className="hover:text-orange-400">Register</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
