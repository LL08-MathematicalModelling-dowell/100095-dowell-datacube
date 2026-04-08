import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

// Reusable API endpoint (adjust if your base URL differs)
const API_BASE = '/api/v2';

interface FileMetadata {
  _id: string;
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  storage_type: string;
  uploaded_at: string;
  updated_at: string;
  user_id: string;
  signed_url: string;
  // Optional fields from GridFS
  length?: number;
  upload_date?: string;
  metadata?: {
    contentType?: string;
    user_id?: string;
  };
}

const FileDetail = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fetch file metadata (the API returns { success: true, info: {...} })
  const { data: file, isLoading, error } = useQuery<FileMetadata>({
    queryKey: ['file', fileId],
    queryFn: async () => {
      const res = await api.get(`${API_BASE}/files/${fileId}/`);
      // Assuming response: { success: true, info: {...} }
      return res.info;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`${API_BASE}/files/${fileId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      navigate('/dashboard/overview');
    },
  });

  // Download using the signed URL from the file metadata
  const downloadFile = () => {
    if (!file?.signed_url) {
      alert('Signed URL not available. Please refresh and try again.');
      return;
    }
    // The signed URL is absolute (or relative) – open it directly
    window.open(file.signed_url, '_blank');
  };

  // Copy text to clipboard
  const copyToClipboard = (text: string, label: string = 'Copied!') => {
    navigator.clipboard.writeText(text);
    alert(label);
  };

  // Format file size
  const formatSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Check if file is an image for preview
  const isImage = file?.content_type?.startsWith('image/');
  const isVideo = file?.content_type?.startsWith('video/');
  const isAudio = file?.content_type?.startsWith('audio/');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (error || !file) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <p className="text-xl mb-4">File not found or access denied.</p>
        <button onClick={() => navigate('/dashboard/overview')} className="text-cyan-400">
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-4 sm:p-10 font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="text-slate-400 hover:text-cyan-400 mb-8 transition-colors flex items-center gap-2 group"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="group-hover:-translate-x-1 transition-transform"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Files
        </button>

        <div className="bg-slate-800 rounded-3xl border border-slate-700/50 shadow-2xl overflow-hidden">
          {/* Header Section */}
          <div className="p-8 bg-slate-700/20 border-b border-slate-700/50 flex items-start justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="h-20 w-20 bg-slate-900 rounded-2xl flex items-center justify-center text-cyan-400 border border-slate-700">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2 break-all">{file.filename}</h1>
                <div className="flex flex-wrap items-center gap-2 text-slate-400 font-mono text-sm">
                  <span className="truncate max-w-[200px]">ID: {file.file_id}</span>
                  <button
                    onClick={() => copyToClipboard(file.file_id, 'File ID copied!')}
                    className="hover:text-cyan-400"
                    title="Copy file ID"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                if (confirm('Delete permanently? This action cannot be undone.'))
                  deleteMutation.mutate();
              }}
              className="text-slate-500 hover:text-red-500 transition-colors p-2"
              title="Delete File"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          </div>

          <div className="p-8">
            {/* Preview for images */}
            {isImage && file.signed_url && (
              <div className="mb-8 bg-slate-900/50 rounded-xl p-4 flex justify-center">
                <img
                  src={`http://127.0.0.1:8000${file.signed_url}`}
                  alt={file.filename}
                  className="max-w-full max-h-96 rounded-lg shadow-lg"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            )}

            {/* Quick preview links for video/audio */}
            {(isVideo || isAudio) && file.signed_url && (
              <div className="mb-8 bg-slate-900/50 rounded-xl p-4">
                <p className="text-slate-300 text-sm mb-2">Preview (streaming):</p>
                {isVideo && (
                  <video controls className="w-full rounded-lg" src={file.signed_url} />
                )}
                {isAudio && (
                  <audio controls className="w-full" src={file.signed_url} />
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
              {/* Left Column */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                    File Properties
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Content Type</span>
                      <span className="text-slate-200">{file.content_type || 'application/octet-stream'}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">File Size</span>
                      <span className="text-slate-200">{formatSize(file.length ?? 0)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Storage Type</span>
                      <span className="text-slate-200">{file.storage_type || 'GridFS'}</span> 
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                    Ownership & IDs
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Owner ID</span>
                      <div className="flex items-center gap-2">
                        <span className="text-cyan-400/80 font-mono text-xs">{file.metadata?.user_id?.substring(0, 10)}...</span>
                        <button
                          onClick={() => {
                            if (file.metadata?.user_id) {
                              copyToClipboard(file.metadata.user_id, 'Owner ID copied!');
                              } else {
                              alert('Owner ID not available');
                            }
                          }}
                          className="hover:text-cyan-400"
                          title="Copy owner ID"
                        >
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    {/* <div className="flex justify-between items-center py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Metadata ID</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-slate-400">{file._id}</span>
                        <button
                          onClick={() => copyToClipboard(file._id, 'Metadata ID copied!')}
                          className="hover:text-cyan-400"
                          title="Copy metadata ID"
                        >
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                        </button>
                      </div>
                    </div> */}
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                    Timeline
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Uploaded On</span>
                      <span className="text-slate-200">
                        {file.upload_date ? new Date(file.upload_date).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Uploaded At</span>
                      <span className="text-slate-200">
                        {file.upload_date ? new Date(file.upload_date).toLocaleTimeString() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Last Updated</span>
                      <span className="text-slate-200">
                        {file.upload_date ? new Date(file.upload_date).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-cyan-500/5 border border-cyan-500/20 p-4 rounded-xl">
                  <p className="text-xs text-cyan-400 leading-relaxed">
                    <strong>Signed URL</strong> (expires in 24 Hours):<br />
                    <span className="break-all text-slate-300 text-[11px] font-mono">
                      {file.signed_url}
                    </span>
                    <button
                      onClick={() => copyToClipboard(file.signed_url, 'Signed URL copied!')}
                      className="ml-2 text-cyan-400 hover:text-cyan-300"
                      title="Copy signed URL"
                    >
                      Copy
                    </button>
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={downloadFile}
                className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white py-4 rounded-xl font-bold transition-all shadow-lg shadow-cyan-900/40 flex items-center justify-center gap-3"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download File
              </button>

              <button
                onClick={() => navigate('/dashboard/overview')}
                className="px-8 bg-slate-700 hover:bg-slate-600 text-slate-200 py-4 rounded-xl font-bold transition-all"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileDetail;