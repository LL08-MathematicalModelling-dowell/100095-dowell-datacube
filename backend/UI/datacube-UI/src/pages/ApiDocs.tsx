import React, { useEffect, useRef, useState, type JSX } from 'react';
import { apiDocs } from "../store/ApiTypes";


interface Method {
  method: string;
  params?: string;
  body?: string;
  response: string;
}

interface Endpoint {
  name: string;
  description: string;
  url: string;
  methods: Method[];
}

interface ApiGroup {
  group: string;
  description: string;
  auth_header?: string;
  how_to_get_key?: string;
  endpoints: Endpoint[];
}

interface CopyButtonProps {
  textToCopy: string;
}

const CopyButton: React.FC<CopyButtonProps> = ({ textToCopy }) => {
  const [isCopied, setIsCopied] = useState(false);
  
  const handleCopy = () => {
    const textArea = document.createElement('textarea');
    textArea.value = textToCopy;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
    document.body.removeChild(textArea);
  };

  return (
    <button onClick={handleCopy} className="absolute top-2 right-2 p-1.5 bg-slate-700/80 rounded-md text-slate-400 hover:text-white hover:bg-slate-600/80 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500" aria-label="Copy to clipboard">
      {isCopied ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400"><path d="M20 6 9 17l-5-5" /></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></svg>
      )}
    </button>
  );
};

interface MethodBadgeProps {
  method: string;
}

const MethodBadge: React.FC<MethodBadgeProps> = ({ method }) => {
  // Define possible HTTP verbs explicitly
  type HttpVerb = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  const verb: HttpVerb = method.split(' ')[0].toUpperCase() as HttpVerb;

  const baseClasses = "text-xs font-bold px-2 py-1 rounded-md shadow-md flex-shrink-0";
  const colors: Record<HttpVerb, string> = {
    GET: "bg-emerald-500/20 text-emerald-400", 
    POST: "bg-sky-500/20 text-sky-400",
    PUT: "bg-amber-500/20 text-amber-400", 
    DELETE: "bg-red-500/20 text-red-400",
    PATCH: "bg-purple-500/20 text-purple-400",
  };
  
  const colorClass = colors[verb] || "bg-slate-500/20 text-slate-400";
  
  return <span className={`${baseClasses} ${colorClass}`}>{verb}</span>;
};

interface CodeBlockProps {
  code: string | undefined | null;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ code }) => {
  if (!code) return null;
  return (
    <div className="relative mt-2">
      {/* Scrollable container for pre and code for better mobile experience */}
      <pre className="bg-slate-800/70 p-4 rounded-lg text-sm text-slate-200 overflow-x-auto border border-slate-700">
        <code className="text-wrap break-words">{code}</code>
      </pre>
      <CopyButton textToCopy={code} />
    </div>
  );
};

interface AuthenticationInfoProps {
  group: ApiGroup;
}

const AuthenticationInfo: React.FC<AuthenticationInfoProps> = ({ group }) => {
  if (!group.auth_header && !group.how_to_get_key) return null;
  return (
    <div className="mt-8 p-4 bg-sky-900/40 border border-sky-800 rounded-lg text-sm shadow-xl">
      <h3 className="text-xl font-semibold text-sky-300 mb-3">Authentication</h3>
      {group.auth_header && (
        <div className="mt-2">
          <h4 className="font-semibold text-sky-300 mb-1">Authorization Header Example</h4>
          <CodeBlock code={group.auth_header} />
        </div>
      )}
      {group.how_to_get_key && (
        <div className={group.auth_header ? 'mt-4' : 'mt-2'}>
          <p className="text-slate-300 leading-relaxed">{group.how_to_get_key}</p>
        </div>
      )}
    </div>
  );
};

export default function App() {
  const initialActiveGroup = apiDocs.length > 0 ? apiDocs[0].group : '';
  const [activeGroup, setActiveGroup] = useState<string>(initialActiveGroup);
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  // Use a Record to type the refs correctly
  const groupRefs = useRef<Record<string, HTMLElement | null>>({});


  // Utility to generate URL-friendly IDs
  const generateId = (text: string): string => text.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

  // Intersection Observer for highlighting the active section in the sidebar
  useEffect(() => {
    const observer = new IntersectionObserver((entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        // Only set active if scrolling down (intersection is near the top)
        if (entry.isIntersecting && entry.boundingClientRect.top < window.innerHeight / 2) {
          setActiveGroup(entry.target.id);
        }
      });
    }, {
      rootMargin: '-50% 0px -50% 0px',
      threshold: 0,
    });

    Object.values(groupRefs.current).forEach(ref => {
      if (ref) observer.observe(ref);
    });

    // Cleanup function
    return () => {
      Object.values(groupRefs.current).forEach(ref => {
        if (ref) observer.unobserve(ref);
      });
    };
  }, []);


  const handleLinkClick = (): void => {
    // Close the mobile menu when a navigation link is clicked
    if (isMenuOpen) {
      setIsMenuOpen(false);
    }
  };

  const MobileMenuButton: JSX.Element = (
    <button
      onClick={() => setIsMenuOpen(!isMenuOpen)}
      className="lg:hidden p-2 rounded-full text-white bg-slate-800/90 hover:bg-slate-700/90 fixed bottom-6 right-6 z-50 shadow-xl transition-all duration-200 hover:scale-110 active:scale-95 focus:outline-none focus:ring-2 focus:ring-cyan-500 backdrop-blur-sm"
      aria-label="Toggle navigation menu"
    >
      {isMenuOpen ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" /></svg>
      )}
    </button>
  );


  return (
    <div className="bg-slate-900 text-slate-300 font-sans min-h-screen">
      {/* Enable smooth scrolling globally */}
      <style>{`html { scroll-behavior: smooth; }`}</style>
      
      {/* Mobile Menu Button - Fixed position */}
      {MobileMenuButton}

      <div className="max-w-7xl mx-auto flex relative">
        
        {/* Mobile Backdrop */}
        {isMenuOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 lg:hidden" 
            onClick={() => setIsMenuOpen(false)} 
            aria-hidden="true" 
          ></div>
        )}

        {/* Sidebar Navigation */}
        <aside 
          className={`
            fixed top-0 left-0 w-64 h-full bg-slate-900 z-40 lg:sticky 
            lg:block lg:w-64 lg:flex-shrink-0 lg:h-screen lg:overflow-y-auto 
            lg:py-10 lg:pr-8 lg:border-r lg:border-slate-800
            transform transition-transform duration-300 ease-in-out
            ${isMenuOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          <div className="p-6 lg:p-0 pt-20 lg:pt-0">
            <h2 className="text-white font-semibold mb-6 text-sm tracking-widest uppercase border-b border-slate-700/50 pb-3">API Reference</h2>
            <nav>
              <ul className="space-y-1">
                {apiDocs.map((group: ApiGroup) => (
                  <li key={group.group}>
                    <a 
                      href={`#${generateId(group.group)}`} 
                      onClick={handleLinkClick}
                      className={`block text-sm px-3 py-2 rounded-lg transition-colors 
                        ${activeGroup === generateId(group.group) 
                          ? 'bg-cyan-500/20 text-cyan-300 font-semibold shadow-inner' 
                          : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-100'
                        }`
                      }
                    >
                      {group.group}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 sm:p-10 lg:pl-10">
          <div className="max-w-4xl">
            {/* Top Header - Adjusted for mobile spacing */}
            <div className="pt-8 lg:pt-0">
              <h1 className="text-4xl font-extrabold text-white tracking-tight">API Reference</h1>
              <p className="mt-4 text-lg text-slate-400">Welcome to the DataCube API. Use our RESTful endpoints to manage your data programmatically.</p>
            </div>

            {/* API Groups */}
            {apiDocs.map((group: ApiGroup) => (
              <section
                key={group.group}
                id={generateId(group.group)}
                ref={el => {
                  groupRefs.current[generateId(group.group)] = el;
                }}
                // Padding for smooth scrolling anchor target below fixed header
                className="pt-16 -mt-16" 
              >
                <h2 className="text-3xl font-bold text-white tracking-tight mt-12">{group.group}</h2>
                <p className="mt-3 text-slate-400 text-lg">{group.description}</p>
                <AuthenticationInfo group={group} />

                {/* Endpoints */}
                {group.endpoints.map((endpoint: Endpoint) => (
                  <article key={endpoint.name} className="mt-10 p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 shadow-2xl">
                    <h3 className="text-xl font-bold text-cyan-400">{endpoint.name}</h3>
                    <p className="mt-2 text-slate-400">{endpoint.description}</p>

                    {endpoint.methods.map((method: Method, index: number) => (
                      <div key={index} className={index > 0 ? "mt-6 border-t border-slate-700/60 pt-6" : "mt-4"}>
                        
                        {/* Method and URL display */}
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-slate-900 p-3 rounded-lg overflow-x-auto border border-slate-800/80">
                          <MethodBadge method={method.method} />
                          <div className='flex-grow min-w-0'>
                            <span className="font-mono text-sm text-slate-300 break-all">{endpoint.url}</span>
                            {method.method.includes("(") && (() => {
                              const match = method.method.match(/\(([^)]+)\)/);
                              return match ? <p className="text-xs text-slate-400 mt-0.5">{match[1]}</p> : null;
                            })()}
                          </div>
                        </div>

                        {/* Request Details */}
                        {method.params && (<div className="mt-4"> <h4 className="font-semibold text-slate-200 text-base">Query Parameters</h4> <CodeBlock code={method.params} /> </div>)}
                        {method.body && (<div className="mt-4"> <h4 className="font-semibold text-slate-200 text-base">Request Body</h4> <CodeBlock code={method.body} /> </div>)}
                        <div className="mt-4"> <h4 className="font-semibold text-slate-200 text-base">Example Response</h4> <CodeBlock code={method.response} /> </div>
                      </div>
                    ))}
                  </article>
                ))}
              </section>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
