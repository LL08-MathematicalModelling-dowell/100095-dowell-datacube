import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import useAuthStore from '../store/authStore';

interface ApiKey {
  _id: string;
  user_id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  key_display: string;
}


interface NewKeyResponse {
  id: string;
  name: string;
  created_on: string;
  key: string;
}

// Reusing the CopyButton component from your API docs if possible, otherwise styled here.
const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [isCopied, setIsCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
      })
      .catch((err) => {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy key.');
      });
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-3 p-1.5 bg-slate-700/80 rounded-md text-slate-400 hover:text-white hover:bg-slate-600/80 transition-all duration-200 flex-shrink-0"
      aria-label="Copy to clipboard"
    >
      {isCopied ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400"><path d="M20 6 9 17l-5-5" /></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></svg>
      )}
    </button>
  );
};

const ApiKeys = () => {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [newKey, setNewKey] = useState<NewKeyResponse | null>(null);
  const [keyName, setKeyName] = useState('');

  // Fetch API keys
  const { data: keys, isLoading, error } = useQuery<ApiKey[]>({
    queryKey: ['apiKeys'],
    queryFn: async () => {
      const response = await api.get('/core/api/v1/keys/');
      return response;
    },
    enabled: !!token, // Only fetch if authenticated
  });

  // Generate new API key
  const generateKeyMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(
        '/core/api/v1/keys/',
        { name: keyName || `Key_${new Date().toISOString()}` }
      );
      return response;
    },
    onSuccess: (data: NewKeyResponse) => {
      setNewKey(data);
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
      setKeyName('');
    },
    onError: (err) => {
      console.error('Failed to generate key:', err);
      alert('Failed to generate key. Please try again.');
    },
  });

  // Delete API key
  const deleteKeyMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(`/core/api/v1/keys/${id}`);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
    onError: (err) => {
      console.error('Failed to delete key:', err);
      alert('Failed to delete key. Please try again.');
    },
  });

  const handleGenerateKey = () => {
    generateKeyMutation.mutate();
  };

  const handleDeleteKey = (id: string) => {
    if (window.confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      deleteKeyMutation.mutate(id);
    }
  };

  return (
    <div className="bg-slate-900 text-slate-300 font-sans min-h-screen p-6 sm:p-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white tracking-tight mb-4">API Keys</h1>
        <p className="mt-4 text-lg text-slate-400 mb-8">
          Manage your API keys to securely authenticate your programmatic requests to the DataCube API.
        </p>

        {/* Generate New Key Section */}
        <div className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8">
          <h2 className="text-2xl font-semibold text-white tracking-tight mb-4">Generate New API Key</h2>
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="Key Name (e.g., 'My_App_Key')"
              className="flex-grow p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
            />
            <button
              onClick={handleGenerateKey}
              disabled={generateKeyMutation.isPending}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-6 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            >
              {generateKeyMutation.isPending ? 'Generating...' : 'Generate New Key'}
            </button>
          </div>
          {generateKeyMutation.isError && (
            <p className="text-red-400 text-sm mt-3">Error generating key. Please try again.</p>
          )}
        </div>

        {/* API Keys Table */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/80 p-6">
          <h2 className="text-2xl font-semibold text-white tracking-tight mb-4">Your Existing API Keys</h2>
          {isLoading && <p className="text-slate-400">Loading API keys...</p>}
          {error && <p className="text-red-400">Error loading API keys. Please try again later.</p>}

          {!isLoading && !error && keys && keys.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-slate-700/60">
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tl-lg">Name</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200">Key</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200">Created On</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tr-lg">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((key) => (
                    <tr key={key._id} className="border-b border-slate-700/60 hover:bg-slate-700/40 transition-colors">
                      <td className="p-3 text-slate-300">{key.name}</td>
                      <td className="p-3">
                        <div className="flex items-center">
                          <code className="text-slate-200 text-sm sm:text-base font-mono overflow-x-auto break-all">
                            {key.key_display}
                          </code>
                        </div>
                      </td>
                      <td className="p-3 text-slate-400">{new Date(key.created_at).toLocaleDateString()}</td>
                      <td className="p-3">
                        <button
                          onClick={() => handleDeleteKey(key._id)}
                          disabled={deleteKeyMutation.isPending}
                          className="text-red-500 hover:text-red-400 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {deleteKeyMutation.isPending ? 'Deleting...' : 'Delete'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !isLoading && !error && (
            <p className="text-slate-400">No API keys found. Generate one to get started!</p>
          )}
        </div>

        {/* New Key Modal */}
        {newKey && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800/90 p-8 rounded-lg shadow-2xl border border-cyan-700 max-w-lg w-full text-center">
              <h2 className="text-3xl font-bold text-white mb-4">API Key Generated!</h2>
              <p className="mb-6 text-slate-300 leading-relaxed">
                Please copy your new API key immediately. For security reasons, this is the **only time** it will be displayed. Do not lose it!
              </p>
              <div className="bg-slate-900/70 p-4 rounded-lg flex items-center justify-between gap-3 mb-6 border border-cyan-800">
                <code className="flex-grow text-slate-200 text-sm sm:text-base font-mono overflow-x-auto break-all">
                  {newKey.key}
                </code>
                <CopyButton text={newKey.key} />
              </div>
              <button
                onClick={() => setNewKey(null)}
                className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-8 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                I have copied my key
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeys;