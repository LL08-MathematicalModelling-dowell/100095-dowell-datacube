/* eslint-disable @typescript-eslint/no-explicit-any */
import type { Monaco } from "@monaco-editor/react";
import Editor from "@monaco-editor/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Copy,
  Edit2,
  FileJson,
  GitCompare,
  Loader2,
  RefreshCw,
  Save,
  Trash2,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";
import { JsonTreeView } from "../components/documents/JsonTreeView";
import { cn } from "../lib/cn";
import api from "../services/api";
import { useThemeStore } from "../store/themeStore";

interface Document {
  _id: string;
  [key: string]: any;
}

const CRUD_URL = "/api/v2/crud/";

const CollectionDocuments = () => {
  const { dbId, collName } = useParams<{ dbId: string; collName: string }>();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [isValidJson, setIsValidJson] = useState(true);
  const [editorContent, setEditorContent] = useState("");

  const originalJson = useRef<string>("");
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ["documents", dbId, collName, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        database_id: dbId!,
        collection_name: collName!,
        page: page.toString(),
        page_size: "25",
      });
      return api.get(`${CRUD_URL}?${params}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) =>
      api.delete(CRUD_URL, {
        database_id: dbId,
        collection_name: collName,
        filters: { _id: docId },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document deleted");
      setSelectedId(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { _id: string; body: Record<string, unknown> }) =>
      api.put(CRUD_URL, {
        database_id: dbId,
        collection_name: collName,
        filters: { _id: payload._id },
        update_data: { $set: payload.body },
        update_all_fields: false,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setIsEditing(false);
      toast.success("Document updated");
    },
    onError: () => toast.error("Update failed — check JSON and permissions"),
  });

  const docs: Document[] = data?.data || [];
  const pagination = data?.pagination;
  const selectedDoc = docs.find((d) => d._id === selectedId) ?? null;

  useEffect(() => {
    if (!selectedId && docs.length > 0) {
      setSelectedId(docs[0]._id);
    }
  }, [docs, selectedId]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied");
  };

  const applyMonacoTheme = useCallback(
    (monaco: Monaco) => {
      const isLight =
        document.documentElement.dataset.theme === "light";
      monaco.editor.defineTheme("datacube-dark", {
        base: "vs-dark",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": "#111827",
          "editorLineNumber.foreground": "#4b5563",
          "editorGutter.background": "#1f2937",
        },
      });
      monaco.editor.defineTheme("datacube-light", {
        base: "vs",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": "#f8fafc",
          "editorLineNumber.foreground": "#94a3b8",
          "editorGutter.background": "#f1f5f9",
        },
      });
      monaco.editor.setTheme(isLight ? "datacube-light" : "datacube-dark");
    },
    []
  );

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    applyMonacoTheme(monaco);
  };

  const themeMode = useThemeStore((s) => s.mode);

  useEffect(() => {
    if (monacoRef.current) applyMonacoTheme(monacoRef.current);
  }, [themeMode, applyMonacoTheme]);

  const openEdit = (doc: Document) => {
    setSelectedId(doc._id);
    const withoutId = Object.fromEntries(
      Object.entries(doc).filter(([k]) => k !== "_id")
    );
    const json = JSON.stringify(withoutId, null, 2);
    originalJson.current = json;
    setEditorContent(json);
    setIsValidJson(true);
    setShowDiff(false);
    setIsEditing(true);
  };

  const handleEditorChange = (value: string | undefined) => {
    const v = value ?? "";
    setEditorContent(v);
    try {
      JSON.parse(v);
      setIsValidJson(true);
    } catch {
      setIsValidJson(false);
    }
  };

  const handleSave = () => {
    if (!isValidJson || !selectedDoc) return;
    try {
      const body = JSON.parse(editorContent);
      if (typeof body !== "object" || body === null || Array.isArray(body)) {
        toast.error("Root must be a JSON object");
        return;
      }
      updateMutation.mutate({ _id: selectedDoc._id, body });
    } catch {
      toast.error("Invalid JSON");
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-[var(--accent-bright)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-20 text-center">
        <AlertCircle className="mx-auto mb-4 h-14 w-14 text-[var(--danger)]" />
        <p className="text-lg text-[var(--text-muted)]">Could not load documents</p>
      </div>
    );
  }

  const displayDoc =
    selectedDoc ?? (docs[0] || null);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Link
            to={`/dashboard/database/${dbId}`}
            className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-[var(--accent-bright)] transition-colors hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to database
          </Link>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            <span className="font-[var(--font-mono)] text-[var(--accent-bright)]">
              {collName}
            </span>
          </h1>
          <p className="mt-1 text-[var(--text-muted)]">
            {pagination?.total_items ?? 0} documents
            {isFetching && (
              <RefreshCw className="ml-2 inline h-3.5 w-3.5 animate-spin" />
            )}
          </p>
        </div>
      </div>

      {docs.length === 0 ? (
        <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--border)] bg-[var(--surface-1)] py-20 text-center">
          <FileJson className="mx-auto mb-4 h-16 w-16 text-[var(--text-subtle)] opacity-40" />
          <p className="text-[var(--text-muted)]">No documents in this collection</p>
        </div>
      ) : (
        <div className="grid min-h-[560px] gap-4 lg:grid-cols-[minmax(260px,320px)_1fr]">
          {/* Document list — Compass-style */}
          <aside className="flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-sm)]">
            <div className="border-b border-[var(--border-subtle)] px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-subtle)]">
                Documents
              </p>
            </div>
            <ul className="flex-1 overflow-y-auto p-2">
              {docs.map((doc) => {
                const active = doc._id === (selectedId || displayDoc?._id);
                return (
                  <li key={doc._id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(doc._id)}
                      className={cn(
                        "mb-1 flex w-full flex-col rounded-[var(--radius-md)] border px-3 py-2.5 text-left transition-all duration-150",
                        active
                          ? "border-[var(--accent)]/40 bg-[var(--accent-soft)]"
                          : "border-transparent hover:bg-[var(--surface-2)]/60"
                      )}
                    >
                      <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-subtle)]">
                        _id
                      </span>
                      <span className="truncate font-[var(--font-mono)] text-xs text-[var(--text-primary)]">
                        {doc._id}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
            {pagination && pagination.total_pages > 1 && (
              <div className="flex items-center justify-between border-t border-[var(--border-subtle)] px-3 py-2">
                <span className="text-xs text-[var(--text-muted)]">
                  Page {page} / {pagination.total_pages}
                </span>
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-2)] disabled:opacity-40"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setPage((p) =>
                        Math.min(pagination.total_pages, p + 1)
                      )
                    }
                    disabled={page === pagination.total_pages}
                    className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-2)] disabled:opacity-40"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </aside>

          {/* Detail panel */}
          {displayDoc && (
            <section className="flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-sm)] overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)] bg-[var(--surface-0)]/50 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] font-semibold uppercase text-[var(--text-subtle)]">
                    BSON preview
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <code className="truncate font-[var(--font-mono)] text-sm text-[var(--accent-bright)]">
                      {displayDoc._id}
                    </code>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(displayDoc._id)}
                      className="shrink-0 rounded p-1 text-[var(--text-muted)] hover:text-[var(--accent-bright)]"
                      aria-label="Copy id"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => openEdit(displayDoc)}
                    className="inline-flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white shadow-sm transition-transform hover:brightness-110 active:scale-[0.98]"
                  >
                    <Edit2 className="h-4 w-4" />
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (
                        confirm(
                          "Delete this document? This may be a soft-delete depending on server settings."
                        )
                      ) {
                        deleteMutation.mutate(displayDoc._id);
                      }
                    }}
                    className="inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--danger-soft)] px-3 py-2 text-sm font-medium text-[var(--danger)] transition-colors hover:bg-[var(--danger-soft)]"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <JsonTreeView
                  data={
                    Object.fromEntries(
                      Object.entries(displayDoc).filter(([k]) => k !== "_id")
                    )
                  }
                  maxDepth={10}
                  className="max-h-none min-h-[320px]"
                />
              </div>
            </section>
          )}
        </div>
      )}

      <AnimatePresence>
        {isEditing && selectedDoc && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--overlay)] p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-md)]"
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 28 }}
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)] px-4 py-3">
                <div>
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                    Edit document
                  </h2>
                  <p className="font-[var(--font-mono)] text-xs text-[var(--text-muted)]">
                    {selectedDoc._id}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {isValidJson ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--chart-1)]">
                      <CheckCircle className="h-4 w-4" /> Valid JSON
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--danger)]">
                      <XCircle className="h-4 w-4" /> Invalid
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowDiff((d) => !d)}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-colors",
                      showDiff
                        ? "bg-[var(--accent-soft)] text-[var(--accent-bright)]"
                        : "bg-[var(--surface-2)] text-[var(--text-primary)]"
                    )}
                  >
                    <GitCompare className="h-4 w-4" />
                    Diff
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={!isValidJson || updateMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {updateMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="rounded-[var(--radius-md)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-2)]"
                  >
                    Close
                  </button>
                </div>
              </div>

              <div className="grid min-h-[420px] flex-1 grid-cols-1 overflow-hidden md:grid-cols-2">
                <div className={cn("border-[var(--border-subtle)] md:border-r", showDiff ? "block" : "md:col-span-2")}>
                  <p className="bg-[var(--surface-0)] px-3 py-2 text-[11px] font-semibold uppercase text-[var(--text-subtle)]">
                    {showDiff ? "New ($set)" : "Editor"}
                  </p>
                  <div className="h-[min(50vh,420px)]">
                    <Editor
                      height="100%"
                      defaultLanguage="json"
                      value={editorContent}
                      onChange={handleEditorChange}
                      onMount={handleEditorDidMount}
                      theme="vs-dark"
                      options={{
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 13,
                        fontFamily: "var(--font-mono)",
                        wordWrap: "on",
                        automaticLayout: true,
                        folding: true,
                        lineNumbers: "on",
                        tabSize: 2,
                      }}
                    />
                  </div>
                </div>
                {showDiff && (
                  <div>
                    <p className="bg-[var(--surface-0)] px-3 py-2 text-[11px] font-semibold uppercase text-[var(--text-subtle)]">
                      Original
                    </p>
                    <div className="h-[min(50vh,420px)]">
                      <Editor
                        height="100%"
                        defaultLanguage="json"
                        value={originalJson.current}
                        onMount={(_e, m) => applyMonacoTheme(m)}
                        theme="vs-dark"
                        options={{
                          readOnly: true,
                          minimap: { enabled: false },
                          fontSize: 13,
                          fontFamily: "var(--font-mono)",
                          wordWrap: "on",
                          automaticLayout: true,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CollectionDocuments;
