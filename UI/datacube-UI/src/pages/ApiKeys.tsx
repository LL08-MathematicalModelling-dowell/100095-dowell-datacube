import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { Card, PageHeader } from "../components/ui/Card.tsx";
import { QueryErrorBlock, RefreshButton } from "../components/ui/QueryRefresh.tsx";
import { cn } from "../lib/cn.ts";
import { btnPrimaryCn, inputCn } from "../lib/uiClasses.ts";
import api from "../services/api";
import useAuthStore from "../store/authStore";

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

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [isCopied, setIsCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setIsCopied(true);
        toast.success("Copied to clipboard");
        setTimeout(() => setIsCopied(false), 2000);
      })
      .catch(() => {
        toast.error("Could not copy");
      });
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={cn(
        "ml-3 shrink-0 rounded-[var(--radius-sm)] p-1.5 transition-colors",
        "bg-[var(--surface-2)] text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text-primary)]"
      )}
      aria-label="Copy to clipboard"
    >
      {isCopied ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-[var(--accent-bright)]"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
          <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
        </svg>
      )}
    </button>
  );
};

const ApiKeys = () => {
  const { accessToken } = useAuthStore();
  const queryClient = useQueryClient();
  const [newKey, setNewKey] = useState<NewKeyResponse | null>(null);
  const [keyName, setKeyName] = useState("");

  const {
    data: keys,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useQuery<ApiKey[]>({
    queryKey: ["apiKeys"],
    queryFn: async () => {
      const response = await api.get("/core/api/v1/keys/");
      return response;
    },
    enabled: !!accessToken,
  });

  const isRefreshing = isFetching && !isLoading;

  const generateKeyMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post("/core/api/v1/keys/", {
        name: keyName || `Key_${new Date().toISOString()}`,
      });
      return response;
    },
    onSuccess: (data: NewKeyResponse) => {
      setNewKey(data);
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      setKeyName("");
      toast.success("API key created");
    },
    onError: () => {
      toast.error("Failed to generate key");
    },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(`/core/api/v1/keys/${id}`);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      toast.success("API key removed");
    },
    onError: () => {
      toast.error("Failed to delete key");
    },
  });

  const handleGenerateKey = () => {
    generateKeyMutation.mutate();
  };

  const handleDeleteKey = (id: string) => {
    if (
      window.confirm(
        "Delete this API key? Apps using it will lose access immediately."
      )
    ) {
      deleteKeyMutation.mutate(id);
    }
  };

  return (
    <div className="min-h-0 font-[var(--font-sans)] text-[var(--text-primary)]">
      <PageHeader
        title="API keys"
        description="Create and revoke keys for programmatic access to the DataCube API."
      />

      <Card
        title="Generate key"
        subtitle="Choose a label you will recognize in logs and dashboards."
        className="mb-8"
      >
        <div className="flex flex-col items-stretch gap-4 sm:flex-row sm:items-center">
          <input
            type="text"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            placeholder="e.g. production-etl"
            className={cn(inputCn(), "flex-1")}
          />
          <button
            type="button"
            onClick={handleGenerateKey}
            disabled={generateKeyMutation.isPending}
            className={btnPrimaryCn("w-full shrink-0 sm:w-auto")}
          >
            {generateKeyMutation.isPending ? "Generating…" : "Generate key"}
          </button>
        </div>
        {generateKeyMutation.isError && (
          <p className="mt-3 text-sm text-[var(--danger)]">
            Something went wrong. Try again.
          </p>
        )}
      </Card>

      <Card
        title="Your keys"
        subtitle="Full secrets are only shown once after creation."
        action={
          <RefreshButton
            onClick={() => refetch()}
            isRefreshing={isRefreshing}
            label="Reload keys"
          />
        }
      >
        {isLoading && (
          <p className="text-[var(--text-muted)]">Loading…</p>
        )}
        {isError && (
          <QueryErrorBlock
            message="Could not load API keys."
            onRetry={() => refetch()}
            isRefreshing={isRefreshing}
          />
        )}

        {!isLoading && !isError && keys && keys.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border-subtle)] bg-[var(--surface-0)]">
                  <th className="p-3 font-semibold text-[var(--text-primary)]">
                    Name
                  </th>
                  <th className="p-3 font-semibold text-[var(--text-primary)]">
                    Preview
                  </th>
                  <th className="p-3 font-semibold text-[var(--text-primary)]">
                    Created
                  </th>
                  <th className="p-3 font-semibold text-[var(--text-primary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr
                    key={key._id}
                    className="border-b border-[var(--border-subtle)] transition-colors hover:bg-[var(--surface-0)]/80"
                  >
                    <td className="p-3 text-[var(--text-primary)]">{key.name}</td>
                    <td className="p-3">
                      <code className="font-mono text-xs break-all text-[var(--text-muted)] sm:text-sm">
                        {key.key_display}
                      </code>
                    </td>
                    <td className="p-3 text-[var(--text-muted)]">
                      {new Date(key.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3">
                      <button
                        type="button"
                        onClick={() => handleDeleteKey(key._id)}
                        disabled={deleteKeyMutation.isPending}
                        className="font-medium text-[var(--danger)] transition-colors hover:underline disabled:opacity-50"
                      >
                        {deleteKeyMutation.isPending ? "…" : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {!isLoading && !isError && (!keys || keys.length === 0) ? (
          <p className="text-[var(--text-muted)]">
            No keys yet. Generate one to call the API from scripts or services.
          </p>
        ) : null}
      </Card>

      {newKey && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--overlay)] p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="new-key-title"
        >
          <div
            className={cn(
              "w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-8 text-center shadow-[var(--shadow-md)]"
            )}
          >
            <h2
              id="new-key-title"
              className="mb-4 text-2xl font-bold text-[var(--text-primary)]"
            >
              Save this secret
            </h2>
            <p className="mb-6 leading-relaxed text-[var(--text-muted)]">
              Copy your key now. For security, it will not be shown again.
            </p>
            <div className="mb-6 flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4">
              <code className="grow break-all font-mono text-sm text-[var(--text-primary)]">
                {newKey.key}
              </code>
              <CopyButton text={newKey.key} />
            </div>
            <button
              type="button"
              onClick={() => setNewKey(null)}
              className={btnPrimaryCn("mx-auto w-auto px-8")}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiKeys;
