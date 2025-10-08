import { apiDocs } from '../store/ApiTypes';
// import type { ApiGroup } from '../store/ApiTypes';
import { useState, useEffect, useRef } from 'react';


const CopyButton: React.FC<{ textToCopy: string }> = ({ textToCopy }) => {
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
    <button onClick={handleCopy} className="absolute top-2 right-2 p-1.5 bg-slate-700/80 rounded-md text-slate-400 hover:text-white hover:bg-slate-600/80 transition-all duration-200" aria-label="Copy to clipboard">
      {isCopied ? (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400"><path d="M20 6 9 17l-5-5" /></svg>) : (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></svg>)}
    </button>
  );
};

const MethodBadge: React.FC<{ method: string }> = ({ method }) => {
  type HttpVerb = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  const verb = method.split(' ')[0].toUpperCase() as HttpVerb;
  const baseClasses = "text-xs font-bold px-2 py-1 rounded-md";
  const colors: Record<HttpVerb, string> = {
    GET: "bg-emerald-500/10 text-emerald-400", POST: "bg-sky-500/10 text-sky-400",
    PUT: "bg-amber-500/10 text-amber-400", DELETE: "bg-red-500/10 text-red-400",
    PATCH: "bg-purple-500/10 text-purple-400",
  };
  return <span className={`${baseClasses} ${colors[verb] || "bg-slate-500/10 text-slate-400"}`}>{verb}</span>;
};

const CodeBlock: React.FC<{ code: string }> = ({ code }) => {
  if (!code) return null;
  return (
    <div className="relative mt-2">
      <pre className="bg-slate-800/70 p-4 rounded-lg text-sm text-slate-200 overflow-x-auto"><code>{code}</code></pre>
      <CopyButton textToCopy={code} />
    </div>
  );
};

interface ApiGroup {
  auth_header?: string;
  how_to_get_key?: string;
  // Add other properties if needed
}

const AuthenticationInfo: React.FC<{ group: ApiGroup }> = ({ group }) => {
  if (!group.auth_header && !group.how_to_get_key) return null;
  return (
    <div className="mt-6 p-4 bg-sky-900/40 border border-sky-800/60 rounded-lg text-sm">
      {group.auth_header && (
        <div>
          <h4 className="font-semibold text-sky-300 mb-1">Authentication Header</h4>
          <CodeBlock code={group.auth_header} />
        </div>
      )}
      {group.how_to_get_key && (
        <div className={group.auth_header ? 'mt-4' : ''}>
          <p className="text-slate-300 leading-relaxed">{group.how_to_get_key}</p>
        </div>
      )}
    </div>
  );
};


// --- MAIN COMPONENT ---

export default function ApiDocsPage() {
  const [activeGroup, setActiveGroup] = useState(apiDocs[0]?.group || '');
  const groupRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => { entries.forEach((entry) => { if (entry.isIntersecting) { setActiveGroup(entry.target.id); } }); }, { rootMargin: '-50% 0px -50% 0px' });
    Object.values(groupRefs.current).forEach(ref => { if (ref) observer.observe(ref); });
    return () => { Object.values(groupRefs.current).forEach(ref => { if (ref) observer.unobserve(ref); }); };
  }, []);

  interface GenerateIdFn {
    (text: string): string;
  }
  const generateId: GenerateIdFn = (text) => text.toLowerCase().replace(/\s+/g, '-');

  return (
    <>
      <div className="bg-slate-900 text-slate-300 font-sans min-h-screen">
        <div className="max-w-7xl mx-auto flex">
          <aside className="hidden lg:block w-64 flex-shrink-0 sticky top-0 h-screen overflow-y-auto py-10 pr-8 border-r border-slate-800">
            <h2 className="text-white font-semibold mb-4 text-sm tracking-wide uppercase">API Reference</h2>
            <nav>
              <ul className="space-y-2">
                {apiDocs.map((group) => (
                  <li key={group.group}>
                    <a href={`#${generateId(group.group)}`} className={`block text-sm px-3 py-1.5 rounded-md transition-colors ${activeGroup === generateId(group.group) ? 'bg-cyan-500/10 text-cyan-400 font-semibold' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}>
                      {group.group}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          <main className="flex-1 p-6 sm:p-10">
            <div className="max-w-4xl">
              <h1 className="text-4xl font-bold text-white tracking-tight">API Reference</h1>
              <p className="mt-4 text-lg text-slate-400">Welcome to the DataCube API. Use our RESTful endpoints to manage your data programmatically.</p>

              {apiDocs.map((group) => (
                <section
                  key={group.group}
                  id={generateId(group.group)}
                  ref={el => {
                    groupRefs.current[generateId(group.group)] = el as HTMLElement | null;
                  }}
                  className="pt-20 -mt-4"
                >
                  <h2 className="text-2xl font-semibold text-white tracking-tight">{group.group}</h2>
                  <p className="mt-2 text-slate-400">{group.description}</p>
                  <AuthenticationInfo group={group} />

                  {group.endpoints.map((endpoint) => (
                    <article key={endpoint.name} className="mt-8 p-6 bg-slate-800/50 rounded-xl border border-slate-700/80">
                      <h3 className="text-xl font-semibold text-cyan-400">{endpoint.name}</h3>
                      <p className="mt-1 text-slate-400">{endpoint.description}</p>

                      {endpoint.methods.map((method, index) => (
                        <div key={index} className={endpoint.methods.length > 1 ? "mt-6 border-t border-slate-700/60 pt-6" : "mt-4"}>
                          <div className="flex items-center gap-3 bg-slate-900/50 p-3 rounded-lg overflow-x-auto">
                            <MethodBadge method={method.method} />
                            <div className='flex-grow'>
                              <span className="font-mono text-sm text-slate-300 break-words">{endpoint.url}</span>
                              {method.method.includes("(") && (() => {
                                const match = method.method.match(/\(([^)]+)\)/);
                                return match ? <p className="text-xs text-slate-400 -mt-0.5">{match[1]}</p> : null;
                              })()}
                            </div>
                          </div>

                          {method.params && (<div className="mt-4"> <h4 className="font-semibold text-slate-200 text-sm">Query Parameters</h4> <CodeBlock code={method.params} /> </div>)}
                          {method.body && (<div className="mt-4"> <h4 className="font-semibold text-slate-200 text-sm">Request Body</h4> <CodeBlock code={method.body} /> </div>)}
                          <div className="mt-4"> <h4 className="font-semibold text-slate-200 text-sm">Example Response</h4> <CodeBlock code={method.response} /> </div>
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
      <style>{`html { scroll-behavior: smooth; }`}</style>
    </>
  );
}

