import React, { useEffect, useState } from 'react';
import useAuthStore from '../store/authStore';

// Main NotFound Component
const NotFound = () => {
  // --- STATE ---
  // State to control the fade-in and slide-up animation on load
  const [isMounted, setIsMounted] = useState(false);
  const { isAuthenticated } = useAuthStore();

  // --- EFFECTS ---
  // On component mount, trigger the animation and log a fun message to the console
  useEffect(() => {
    // Set a timeout to allow the component to render before starting the animation
    const timer = setTimeout(() => setIsMounted(true), 100);

    // Easter egg for curious developers
    console.log(
      "🛸 Houston, we have a console log! It seems you've discovered a hidden message in this 404 nebula. No secret commands here, but feel free to explore the DOM!"
    );

    // Cleanup the timer on unmount
    return () => clearTimeout(timer);
  }, []);

  // --- HANDLERS ---
  // Navigate to the previous page in the browser's history
  const handleGoBack = () => {
    window.history.back();
  };

  // A small helper component for the navigation links to avoid repetition
  const IconLink = ({ href, icon, title, subtitle }: { href: string; icon: React.ReactNode; title: string; subtitle: string; }) => (
    <a
      href={href}
      className="group flex items-center p-4 rounded-lg bg-slate-800/50 hover:bg-slate-700/60 border border-slate-700/80 transition-all duration-300 transform hover:-translate-y-1"
      aria-label={`Maps to ${title}`}
    >
      <div className="flex-shrink-0 w-12 h-12 bg-slate-700/50 text-cyan-400 rounded-md flex items-center justify-center mr-4 group-hover:bg-cyan-400 group-hover:text-slate-900 transition-colors duration-300">
        {icon}
      </div>
      <div>
        <p className="font-semibold text-slate-200">{title}</p>
        <p className="text-sm text-slate-400">{subtitle}</p>
      </div>
    </a>
  );

  // --- RENDER ---
  return (
    <>
      <main className="relative flex items-center justify-center min-h-screen w-full bg-slate-900 text-white font-sans overflow-hidden">
        {/* Background decorative elements for a "galaxy" feel */}
        <div className="absolute top-0 left-0 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>

        <div
          className={`
            relative z-10 max-w-2xl w-full mx-4 p-8 sm:p-10 bg-slate-800/50 backdrop-blur-lg 
            rounded-2xl shadow-2xl border border-slate-700/80 transition-all duration-700 ease-out
            ${isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}
          `}
        >
          {/* SVG Illustration: A lost satellite */}
          <div className="flex justify-center mb-6">
            <svg
              className="w-24 h-24 text-cyan-400"
              style={{ animation: 'float 4s ease-in-out infinite' }}
              viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M48.752 34.331C53.31 35.533 56 36.69 56 38.002C56 39.313 53.31 40.47 48.752 41.671L37.333 44.5L32 56L26.667 44.5L15.248 41.671C10.69 40.47 8 39.313 8 38.002C8 36.69 10.69 35.533 15.248 34.331L26.667 31.5L32 20L37.333 31.5L48.752 34.331Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M32 8V20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M22.05 22.05L26.667 26.667" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M8 32H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="48" cy="16" r="4" fill="currentColor" fillOpacity="0.3" />
              <circle cx="12" cy="52" r="2" fill="currentColor" fillOpacity="0.3" />
            </svg>
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-500 mb-4 text-center tracking-tight">
            404 - Lost in Space
          </h1>

          <p className="mb-8 text-base sm:text-lg text-slate-400 leading-relaxed text-center max-w-md mx-auto">
            It seems you've drifted into an uncharted quadrant of the web. The page you're looking for might have been moved, deleted, or perhaps it never existed.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mb-10">
            <button
              onClick={handleGoBack}
              className="w-full sm:w-auto bg-cyan-500 text-slate-900 font-semibold px-6 py-3 rounded-lg hover:bg-cyan-400 transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-cyan-500/50"
              aria-label="Go back to the previous page"
            >
              Go Back
            </button>
            <a
              href="/"
              className="w-full sm:w-auto bg-slate-700/80 text-white font-semibold px-6 py-3 rounded-lg hover:bg-slate-600/80 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-slate-500/50"
              aria-label="Go to the homepage"
            >
              Return Home
            </a>
          </div>

          {/* Suggested Links */}
          <div className="space-y-4">
            <IconLink
              href="/api-docs"
              title="API Documentation"
              subtitle="Your mission control for data."
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v11.494m-9-5.747h18" /></svg>
              }
            />
            {isAuthenticated && (
              <>
                <IconLink
                  href="/api-keys"
                  title="Manage API Keys"
                  subtitle="Your access codes to the galaxy."
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7h3a5 5 0 015 5 5 5 0 01-5 5h-3m-6 0H6a5 5 0 01-5-5 5 5 0 015-5h3" /></svg>
                  }
                />
                <IconLink
                  href="/billing"
                  title="Billing & Subscriptions"
                  subtitle="Refuel your journey here."
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                  }
                />
              </>)
            }

          </div>
        </div>
      </main>

      {/* CSS for custom animations not easily done with Tailwind */}
      <style>
        {`
          @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
          }
          /* A subtle animation for the background gradients */
          .animate-pulse {
             animation: pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite;
           }
           @keyframes pulse {
             50% {
               opacity: 0.5;
             }
           }
        `}
      </style>
    </>
  );
}


export default NotFound;