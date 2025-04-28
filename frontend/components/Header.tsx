// components/Header.js
import Link from 'next/link';

const Header = () => (
    <header className="bg-gray-900 text-white p-4">
        <nav className="container mx-auto flex justify-between items-center">
            <Link href="/" className="text-xl font-bold">API Service</Link>
            <div>
                <Link href="/auth/register" className="bg-orange-500 text-white px-6 py-3 rounded mr-4 hover:bg-orange-400 transition">Register</Link>
                <Link href="/auth/login" className="bg-orange-600 text-white px-6 py-3 rounded hover:bg-orange-500 transition">Login</Link>
            </div>
        </nav>
    </header>
);

export default Header;
