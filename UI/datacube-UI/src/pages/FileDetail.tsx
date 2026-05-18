import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { RefreshButton } from "../components/ui/QueryRefresh";
import { cn } from "../lib/cn";
import api, { API_ORIGIN } from "../services/api";

// Reusable API endpoint (adjust if your base URL differs)
const API_BASE = "/api/v2";

function resolveMediaUrl(signedUrl: string | undefined) {
  if (!signedUrl) return "";
  return signedUrl.startsWith("http") ? signedUrl : `${API_ORIGIN}${signedUrl}`;
}

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
  const { data: file, isLoading, isError, isFetching, refetch } = useQuery<FileMetadata>({
    queryKey: ['file', fileId],
    queryFn: async () => {
      const res = await api.get(`${API_BASE}/files/${fileId}/`);
      return res.info;
    },
  });

  const isRefreshing = isFetching && !isLoading;

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`${API_BASE}/files/${fileId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["files"] });
      toast.success("File deleted");
      navigate("/dashboard/overview");
    },
  });

  // Download using the signed URL from the file metadata
  const downloadFile = () => {
    if (!file?.signed_url) {
      toast.error("Download link not available. Refresh and try again.");
      return;
    }
    window.open(resolveMediaUrl(file.signed_url), "_blank");
  };

  const copyToClipboard = (text: string, message = "Copied") => {
    void navigator.clipboard.writeText(text).then(
      () => toast.success(message),
      () => toast.error("Could not copy")
    );
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
      <div className="flex min-h-[50vh] items-center justify-center bg-[var(--surface-0)]">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-[var(--border-subtle)] border-t-[var(--accent)]" />
      </div>
    );
  }

  if (isError || !file) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center bg-[var(--surface-0)] px-4 text-[var(--text-primary)]">
        <p className="mb-4 text-xl">File not found or access denied.</p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isRefreshing}
            className="inline-flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            Retry
          </button>
          <button
            type="button"
            onClick={() => navigate("/dashboard/overview")}
            className="font-medium text-[var(--accent-bright)] hover:underline"
          >
            Back to overview
          </button>
        </div>
      </div>
    );
  }

  if (!file) {
    return null;
  }

  const previewSrc = resolveMediaUrl(file.signed_url);

  return (
    <div className="min-h-0 bg-[var(--surface-0)] p-0 font-[var(--font-sans)] sm:p-0">
      <div className="mx-auto max-w-4xl">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="group mb-8 flex items-center gap-2 text-[var(--text-muted)] transition-colors hover:text-[var(--accent-bright)]"
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
          Back
        </button>

        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-md)]">
          <div className="flex items-start justify-between gap-6 border-b border-[var(--border-subtle)] bg-[var(--surface-0)]/50 p-8">
            <div className="flex items-center gap-6">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-0)] text-[var(--accent-bright)]">
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
              <div className="min-w-0">
                <h1 className="mb-2 break-all text-3xl font-bold text-[var(--text-primary)]">
                  {file.filename}
                </h1>
                <div className="flex flex-wrap items-center gap-2 font-mono text-sm text-[var(--text-muted)]">
                  <span className="max-w-[200px] truncate">ID: {file.file_id}</span>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(file.file_id, "File ID copied")}
                    className="text-[var(--accent-bright)] hover:opacity-90"
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

            <div className="flex items-center gap-2">
              <RefreshButton
                onClick={() => refetch()}
                isRefreshing={isRefreshing}
                label="Reload"
              />
              <button
              type="button"
              onClick={() => {
                if (
                  window.confirm(
                    "Delete this file permanently? This cannot be undone."
                  )
                )
                  deleteMutation.mutate();
              }}
              className="p-2 text-[var(--text-subtle)] transition-colors hover:text-[var(--danger)]"
              title="Delete file"
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
          </div>

          <div className={cn("p-8", isRefreshing && "opacity-70")}>
            {/* Preview for images */}
            {isImage && previewSrc ? (
              <div className="mb-8 flex justify-center rounded-[var(--radius-md)] bg-[var(--surface-0)] p-4">
                <img
                  src={previewSrc}
                  alt={file.filename}
                  className="max-h-96 max-w-full rounded-lg shadow-[var(--shadow-sm)]"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
            ) : null}

            {(isVideo || isAudio) && previewSrc ? (
              <div className="mb-8 rounded-[var(--radius-md)] bg-[var(--surface-0)] p-4">
                <p className="mb-2 text-sm text-[var(--text-muted)]">Preview</p>
                {isVideo ? (
                  <video
                    controls
                    className="w-full rounded-lg"
                    src={previewSrc}
                  />
                ) : null}
                {isAudio ? <audio controls className="w-full" src={previewSrc} /> : null}
              </div>
            ) : null}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
              {/* Left Column */}
              <div className="space-y-6">
                <div>
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-widest text-[var(--text-subtle)]">
                    File properties
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Content type</span>
                      <span className="text-[var(--text-primary)]">{file.content_type || 'application/octet-stream'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">File size</span>
                      <span className="text-[var(--text-primary)]">{formatSize(file.length ?? 0)}</span>
                    </div>
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Storage</span>
                      <span className="text-[var(--text-primary)]">{file.storage_type || 'GridFS'}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-widest text-[var(--text-subtle)]">
                    Ownership
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Owner ID</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-[var(--accent-bright)]/90">{file.metadata?.user_id?.substring(0, 10)}...</span>
                        <button
                          type="button"
                          onClick={() => {
                            if (file.metadata?.user_id) {
                              copyToClipboard(file.metadata.user_id, "Owner ID copied");
                            } else {
                              toast.error("Owner ID not available");
                            }
                          }}
                          className="text-[var(--accent-bright)] hover:opacity-90"
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
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-widest text-[var(--text-subtle)]">
                    Timeline
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Uploaded on</span>
                      <span className="text-[var(--text-primary)]">
                        {file.upload_date ? new Date(file.upload_date).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Time</span>
                      <span className="text-[var(--text-primary)]">
                        {file.upload_date ? new Date(file.upload_date).toLocaleTimeString() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-[var(--border-subtle)] py-2">
                      <span className="text-[var(--text-muted)]">Full timestamp</span>
                      <span className="text-[var(--text-primary)]">
                        {file.upload_date ? new Date(file.upload_date).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="rounded-[var(--radius-md)] border border-[var(--accent)]/25 bg-[var(--accent-soft)] p-4">
                  <p className="text-xs leading-relaxed text-[var(--text-primary)]">
                    <strong className="text-[var(--accent-bright)]">Signed URL</strong> (time-limited):<br />
                    <span className="break-all font-mono text-[11px] text-[var(--text-muted)]">
                      {file.signed_url}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        if (file.signed_url) {
                          copyToClipboard(file.signed_url, "Signed URL copied");
                        }
                      }}
                      className="ml-2 font-medium text-[var(--accent-bright)] hover:underline"
                      title="Copy signed URL"
                    >
                      Copy
                    </button>
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row">
              <button
                type="button"
                onClick={downloadFile}
                className="flex flex-1 items-center justify-center gap-3 rounded-[var(--radius-md)] bg-[var(--accent)] py-4 font-bold text-white shadow-[var(--shadow-sm)] transition-all hover:opacity-95"
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
                Download
              </button>

              <button
                type="button"
                onClick={() => navigate('/dashboard/overview')}
                className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-8 py-4 font-bold text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-2)]"
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