import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const FileDetail = () => {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: file, isLoading, error } = useQuery({
    queryKey: ['file', fileId],
    queryFn: () => api.get(`/api/files/${fileId}/`).then(res => res.info),
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/api/files/${fileId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      navigate('/dashboard/overview');
    }
  });

  const downloadFile = async () => {
    try {
      const response = await api.get(`/api/files/${fileId}/download/`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file?.filename || 'download');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Download failed');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  if (isLoading) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
    </div>
  );

  if (error || !file) return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
      <p className="text-xl mb-4">File not found or access denied.</p>
      <button onClick={() => navigate('/dashboard/overview')} className="text-cyan-400">Return to Dashboard</button>
    </div>
  );

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-slate-900 p-4 sm:p-10 font-sans">
      <div className="max-w-3xl mx-auto">
        <button 
          onClick={() => navigate(-1)} 
          className="text-slate-400 hover:text-cyan-400 mb-8 transition-colors flex items-center gap-2 group"
        >
          <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:-translate-x-1 transition-transform"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Back to Files
        </button>

        <div className="bg-slate-800 rounded-3xl border border-slate-700/50 shadow-2xl overflow-hidden">
          {/* Header Section */}
          <div className="p-8 bg-slate-700/20 border-b border-slate-700/50 flex items-start justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="h-20 w-20 bg-slate-900 rounded-2xl flex items-center justify-center text-cyan-400 border border-slate-700">
                <svg xmlns="http://www.w3.org" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2 break-all">{file.filename}</h1>
                <div className="flex items-center gap-2 text-slate-400 font-mono text-sm">
                  <span className="truncate max-w-[200px]">{fileId}</span>
                  <button onClick={() => copyToClipboard(fileId!)} className="hover:text-cyan-400">
                    <svg xmlns="http://www.w3.org" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  </button>
                </div>
              </div>
            </div>
            
            <button 
              onClick={() => { if(confirm('Delete permanently?')) deleteMutation.mutate(); }}
              className="text-slate-500 hover:text-red-500 transition-colors p-2"
              title="Delete File"
            >
              <svg xmlns="http://www.w3.org" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            </button>
          </div>

          <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
              {/* Info Column 1 */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">File Properties</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Content Type</span>
                      <span className="text-slate-200">{file.metadata?.contentType || 'application/octet-stream'}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Total Size</span>
                      <span className="text-slate-200">{formatSize(file.length)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Ownership</h3>
                  <div className="flex justify-between py-2 border-b border-slate-700/30">
                    <span className="text-slate-400">Owner ID</span>
                    <span className="text-cyan-400/80 font-mono text-xs">{file.metadata?.user_id}</span>
                  </div>
                </div>
              </div>

              {/* Info Column 2 */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Timeline</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Uploaded On</span>
                      <span className="text-slate-200">{new Date(file.upload_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-slate-700/30">
                      <span className="text-slate-400">Uploaded At</span>
                      <span className="text-slate-200">{new Date(file.upload_date).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-cyan-500/5 border border-cyan-500/20 p-4 rounded-xl">
                  <p className="text-xs text-cyan-400 leading-relaxed italic">
                    This file is stored across multiple chunks in the shared user_storage bucket. 
                    Redundancy and integrity are handled by MongoDB GridFS.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={downloadFile} 
                className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white py-4 rounded-xl font-bold transition-all shadow-lg shadow-cyan-900/40 flex items-center justify-center gap-3"
              >
                <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download Raw Content
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