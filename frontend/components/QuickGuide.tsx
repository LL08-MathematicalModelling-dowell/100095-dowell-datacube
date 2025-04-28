// components/QuickGuide.js
import Link from 'next/link';

const QuickGuide = () => (
    <section className="container mx-auto py-16">
        <h2 className="text-2xl font-semibold text-center text-orange-300 mb-8">Quick Guide to Using the API</h2>
        <ol className="list-decimal list-inside text-lg text-gray-300">
            <li>Register for an account to get started.</li>
            <li>Log in to your account.</li>
            <li>Generate your API key from the dashboard.</li>
            <li>
                Read the{' '}
                <Link href="/api-docs" className="text-orange-500 underline">
                    API Documentation
                </Link>{' '}
                to learn how to use the API.
            </li>
        </ol>
    </section>
);

export default QuickGuide;
