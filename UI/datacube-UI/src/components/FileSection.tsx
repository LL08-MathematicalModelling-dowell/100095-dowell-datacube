import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useState } from 'react';

/** TypeScript Interfaces for the API Response **/
export interface FileMetadata {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  storage_type: 'gridfs';
  uploaded_at: string;
}

export interface FileListResponse {
  success: boolean;
  data: FileMetadata[];
  stats: {
    total_files: number;
    total_storage_bytes: number;
  };
  pagination: {
    current_page: number;
    total_items: number;
    total_pages: number;
  };
}

const FilesSection = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // 1. Fetch Files & Stats
  const { data, isLoading } = useQuery<FileListResponse>({
    queryKey: ['files', page],
    queryFn: async () => {
      const response = await api.get(`/api/v2/files/?page=${page}&page_size=${pageSize}`);
      return response;
    },
    // keepPreviousData: true is deprecated in v5, use placeholderData if on newest TanStack
  });

  const files = data?.data || [];
  const stats = data?.stats || { total_files: 0, total_storage_bytes: 0 };
  const pagination = data?.pagination || { total_pages: 1 };

  // Helper to format bytes
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 2. Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post('/api/v2/files/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      alert('Upload complete!');
    },
    onError: (err: any) => alert(err.response?.data?.detail || 'Upload failed')
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) uploadMutation.mutate(e.target.files[0]);
  };

  return (
    <section className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8 shadow-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white tracking-tight">Cloud Storage</h2>
          <div className="flex items-center gap-4 mt-1">
             <span className="text-xs font-medium px-2 py-1 bg-slate-700 text-cyan-400 rounded-md border border-slate-600">
               {stats.total_files} Files
             </span>
             <span className="text-xs font-medium px-2 py-1 bg-slate-700 text-emerald-400 rounded-md border border-slate-600">
               {formatBytes(stats.total_storage_bytes)} Used
             </span>
          </div>
        </div>
        
        <label className="cursor-pointer bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 px-6 rounded-lg transition-all flex items-center gap-2 shadow-lg shadow-emerald-900/20">
          <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploadMutation.isPending} />
          <svg xmlns="http://www.w3.org" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          {uploadMutation.isPending ? 'Uploading...' : 'Upload File'}
        </label>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="h-16 bg-slate-700/50 rounded-lg" />)}
        </div>
      ) : (
        <div className="space-y-2">
          {files.map((file) => (
            <div 
              key={file.file_id}
              onClick={() => navigate(`/dashboard/files/${file.file_id}`)}
              className="group flex items-center justify-between p-3.5 bg-slate-700/20 border border-slate-700/50 rounded-lg hover:border-cyan-500/50 hover:bg-slate-700/40 cursor-pointer transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 bg-slate-900 rounded-md text-cyan-400 group-hover:bg-cyan-500 group-hover:text-white transition-all">
                  <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div>
                  <p className="text-slate-200 font-medium truncate max-w-[180px] sm:max-w-md">{file.filename}</p>
                  <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
                    {formatBytes(file.size)} • {new Date(file.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center text-slate-600 group-hover:text-cyan-400 transition-colors">
                 <span className="text-xs mr-2 opacity-0 group-hover:opacity-100 transition-opacity">Details</span>
                 <svg xmlns="http://www.w3.org" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </div>
            </div>
          ))}

          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-6 mt-8 pt-6 border-t border-slate-700/50">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="p-2 bg-slate-700/50 rounded-full text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-all"
              >
                <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              
              <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Page <span className="text-white">{page}</span> / {pagination.total_pages}
              </div>

              <button 
                disabled={page >= pagination.total_pages}
                onClick={() => setPage(p => p + 1)}
                className="p-2 bg-slate-700/50 rounded-full text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-all"
              >
                <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          )}

          {!isLoading && files.length === 0 && (
            <div className="text-center py-12 border-2 border-dashed border-slate-700/50 rounded-xl bg-slate-800/20">
              <svg className="mx-auto h-12 w-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <p className="text-slate-500 font-medium">Your storage is empty.</p>
              <p className="text-xs text-slate-600 mt-1">Upload your first file to get started.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default FilesSection;