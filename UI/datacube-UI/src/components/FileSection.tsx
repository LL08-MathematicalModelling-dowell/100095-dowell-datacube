import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { QueryErrorBlock, RefreshButton } from './ui/QueryRefresh';
import { cn } from '../lib/cn';

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
  const { data, isLoading, isError, isFetching, refetch } = useQuery<FileListResponse>({
    queryKey: ['files', page],
    queryFn: async () => {
      const response = await api.get(`/api/v2/files/?page=${page}&page_size=${pageSize}`);
      return response;
    },
  });

  const isRefreshing = isFetching && !isLoading;

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
      toast.success('Upload complete');
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Upload failed'),
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) uploadMutation.mutate(e.target.files[0]);
  };

  return (
    <section className="mb-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)]/80 p-6 shadow-[var(--shadow-sm)]">
      <div className="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[var(--text-primary)]">
            Cloud storage
          </h2>
          <div className="mt-1 flex items-center gap-4">
             <span className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-0)] px-2 py-1 text-xs font-medium text-[var(--info)]">
               {stats.total_files} files
             </span>
             <span className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-0)] px-2 py-1 text-xs font-medium text-[var(--accent-bright)]">
               {formatBytes(stats.total_storage_bytes)} used
             </span>
          </div>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <RefreshButton
            onClick={() => refetch()}
            isRefreshing={isRefreshing}
            label="Reload files"
          />
          <label className="flex cursor-pointer items-center gap-2 rounded-lg bg-[var(--accent)] px-6 py-2.5 font-semibold text-white shadow-[var(--shadow-sm)] transition-all hover:opacity-95">
            <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploadMutation.isPending} />
            <svg xmlns="http://www.w3.org" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            {uploadMutation.isPending ? 'Uploading...' : 'Upload File'}
          </label>
        </div>
      </div>

      {isError ? (
        <QueryErrorBlock
          message="Could not load files."
          onRetry={() => refetch()}
          isRefreshing={isRefreshing}
        />
      ) : isLoading ? (
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-[var(--surface-2)]/50" />)}
        </div>
      ) : (
        <div className={cn('space-y-2', isRefreshing && 'opacity-70')}>
          {files.map((file) => (
            <div 
              key={file.file_id}
              onClick={() => navigate(`/dashboard/files/${file.file_id}`)}
              className="group flex cursor-pointer items-center justify-between rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-0)]/80 p-3.5 transition-all hover:border-[var(--accent)]/40 hover:bg-[var(--surface-2)]/40"
            >
              <div className="flex items-center gap-4">
                <div className="rounded-md bg-[var(--surface-1)] p-2 text-[var(--accent-bright)] transition-all group-hover:bg-[var(--accent)] group-hover:text-white">
                  <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div>
                  <p className="truncate max-w-[180px] font-medium text-[var(--text-primary)] sm:max-w-md">
                    {file.filename}
                  </p>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-subtle)]">
                    {formatBytes(file.size)} •{" "}
                    {new Date(file.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center text-[var(--text-subtle)] transition-colors group-hover:text-[var(--accent-bright)]">
                 <span className="text-xs mr-2 opacity-0 group-hover:opacity-100 transition-opacity">Details</span>
                 <svg xmlns="http://www.w3.org" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </div>
            </div>
          ))}

          {pagination.total_pages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-6 border-t border-[var(--border-subtle)] pt-6">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="rounded-full bg-[var(--surface-2)] p-2 text-[var(--text-muted)] transition-all hover:bg-[var(--surface-elevated)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-20"
              >
                <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              
              <div className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
                Page <span className="text-[var(--text-primary)]">{page}</span> /{" "}
                {pagination.total_pages}
              </div>

              <button 
                disabled={page >= pagination.total_pages}
                onClick={() => setPage(p => p + 1)}
                className="rounded-full bg-[var(--surface-2)] p-2 text-[var(--text-muted)] transition-all hover:bg-[var(--surface-elevated)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-20"
              >
                <svg xmlns="http://www.w3.org" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          )}

          {!isLoading && files.length === 0 && (
            <div className="rounded-xl border-2 border-dashed border-[var(--border-subtle)] bg-[var(--surface-0)]/50 py-12 text-center">
              <svg className="mx-auto mb-3 h-12 w-12 text-[var(--text-subtle)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <p className="font-medium text-[var(--text-muted)]">Your storage is empty.</p>
              <p className="mt-1 text-xs text-[var(--text-subtle)]">Upload your first file to get started.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default FilesSection;