import type { Monaco } from "@monaco-editor/react";
import Editor from "@monaco-editor/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { 
    AlertCircle, CheckCircle,
    ChevronLeft, ChevronRight,
    Copy, Edit2, FileJson,
    GitCompare, Loader2,
    Save, Trash2, XCircle 
} from "lucide-react";
import { useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";
import api from "../services/api";

interface Document {
    _id: string;
    [key: string]: any;
}

const CRUD_URL = "/api/crud/";

const CollectionDocuments = () => {
    // === All hooks at the top — NEVER after conditional returns ===
    const { dbId, collName } = useParams<{ dbId: string; collName: string }>();
    // const navigate = useNavigate();
    const queryClient = useQueryClient();

    const [page, setPage] = useState(1);
    const [search, ] = useState("");
    const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [, setEditValue] = useState("");
    const [showDiff, setShowDiff] = useState(false);
    const [isValidJson, setIsValidJson] = useState(true);
    const [editorContent, setEditorContent] = useState("");


    const originalJson = useRef<string>("");
    const editorRef = useRef<any>(null);
    const monacoRef = useRef<Monaco | null>(null);

    // === Queries & Mutations ===
    const { data, isLoading, error } = useQuery({
        queryKey: ["documents", dbId, collName, page, search],
        queryFn: async () => {
            const params = new URLSearchParams({
                database_id: dbId!,
                collection_name: collName!,
                page: page.toString(),
                page_size: "20",
                ...(search && { filters: JSON.stringify({ $text: { $search: search } }) }),
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
        },
    });

    const updateMutation = useMutation({
        mutationFn: (doc: Document) =>
            api.put(CRUD_URL, {
                database_id: dbId,
                collection_name: collName,
                filters: { _id: doc._id },
                update_data: doc,
                update_all_fields: true,
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["documents"] });
            setIsEditing(false);
            toast.success("Document updated");
        },
        onError: () => toast.error("Invalid JSON or update failed"),
    });

    // === Helper Functions ===
    const docs: Document[] = data?.data || [];
    const pagination = data?.pagination;

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.success("Copied to clipboard!");
    };

    const handleEditorDidMount = (editor: any, monaco: Monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco;

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
        monaco.editor.setTheme("datacube-dark");
    };

    const handleEdit = (doc: Document) => {
        setSelectedDoc(doc);
        originalJson.current = JSON.stringify(doc, null, 2);
        setEditValue(JSON.stringify(
            Object.fromEntries(Object.entries(doc).filter(([k]) => k !== "_id")),
            null,
            2
        ));
        setIsEditing(true);
        setShowDiff(false);
        setIsValidJson(true);
    };


    // const handleEditorChange = (value: string | undefined) => {
    //     if (!value) {
    //         setIsValidJson(false);
    //         return;
    //     }
    //     try {
    //         JSON.parse(value);
    //         setIsValidJson(true);
    //         if (editorRef.current) {
    //             editorRef.current.getAction("editor.action.formatDocument")?.run();
    //         }
    //     } catch {
    //         setIsValidJson(false);
    //     }
    // };

    const handleEditorChange = (value: string | undefined) => {
        const newValue = value || "";
        setEditorContent(newValue); // ← This is what gets saved

        try {
            JSON.parse(newValue);
            setIsValidJson(true);
        } catch {
            setIsValidJson(false);
        }
    };

    const handleSave = () => {
        if (!isValidJson || !selectedDoc) return;

        try {
            const editedData = JSON.parse(editorContent); // ← Use state, not ref
            const fullDocument = {
                ...editedData,
            };

            updateMutation.mutate(fullDocument);
        } catch (err) {
            toast.error("Invalid JSON");
        }
    };

    // === Early Returns (AFTER all hooks) ===
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="w-12 h-12 animate-spin text-[var(--green-dark)]" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-20">
                <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <p className="text-xl text-[var(--text-muted)]">Failed to load documents</p>
            </div>
        );
    }
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <Link
                        to={`/dashboard/database/${dbId}`}
                        className="text-[var(--green-dark)] hover:underline flex items-center gap-2 mb-2"
                    >
                        ← Back to Database
                    </Link>
                    <h1 className="text-3xl font-bold text-[var(--green-dark)]">
                        Collection: <span className="font-mono text-[var(--text-light)]">{collName}</span>
                    </h1>
                    <p className="text-[var(--text-muted)] mt-1">
                        {pagination?.total_items || 0} documents
                    </p>
                </div>

                {/* <div className="flex items-center gap-4 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search documents..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-10 pr-4 py-3 bg-[var(--bg-dark-2)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--green-dark)] transition-colors w-full sm:w-80"
            />
          </div>
        </div> */}
            </div>

            {/* Documents Table */}
            {docs.length === 0 ? (
                <div className="text-center py-20 bg-[var(--bg-dark-2)] rounded-xl border border-dashed border-[var(--border-color)]">
                    <FileJson className="w-20 h-20 text-[var(--text-muted)] mx-auto mb-4 opacity-50" />
                    <p className="text-xl text-[var(--text-muted)]">No documents found</p>
                    <p className="text-[var(--text-muted)] mt-2">Try adjusting your search or add some data!</p>
                </div>
            ) : (
                <div className="bg-[var(--bg-dark-2)] rounded-xl border border-[var(--border-color)] overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[var(--bg-dark-3)]">
                                <tr>
                                    <th className="px-6 py-4 text-left text-sm font-medium text-[var(--text-muted)]">_id</th>
                                    <th className="px-6 py-4 text-left text-sm font-medium text-[var(--text-muted)]">Preview</th>
                                    <th className="px-6 py-4 text-right text-sm font-medium text-[var(--text-muted)]">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[var(--border-color)]">
                                {docs.map((doc) => (
                                    <tr key={doc._id} className="hover:bg-[var(--bg-dark-3)]/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm text-[var(--text-light)]">
                                            <div className="flex items-center gap-2">
                                                <span className="truncate max-w-xs">{doc._id}</span>
                                                <button
                                                    onClick={() => copyToClipboard(doc._id)}
                                                    className="text-[var(--text-muted)] hover:text-[var(--green-dark)]"
                                                >
                                                    <Copy className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <pre className="text-xs text-[var(--text-muted)] font-mono truncate max-w-2xl">
                                                {JSON.stringify({ ...doc, _id: undefined }, null, 2)}
                                            </pre>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleEdit(doc)}
                                                className="text-cyan-400 hover:text-cyan-300 mr-4"
                                            >
                                                <Edit2 className="w-5 h-5" />
                                            </button>
                                            <button
                                                onClick={() => {
                                                    if (confirm("Delete this document?")) {
                                                        deleteMutation.mutate(doc._id);
                                                    }
                                                }}
                                                className="text-red-500 hover:text-red-400"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {pagination && pagination.total_pages > 1 && (
                        <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border-color)]">
                            <p className="text-sm text-[var(--text-muted)]">
                                Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, pagination.total_items)} of {pagination.total_items} documents
                            </p>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="p-2 rounded-lg bg-[var(--bg-dark-3)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-dark-3)]/80 transition-colors"
                                >
                                    <ChevronLeft className="w-5 h-5" />
                                </button>
                                <button
                                    onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                                    disabled={page === pagination.total_pages}
                                    className="p-2 rounded-lg bg-[var(--bg-dark-3)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-dark-3)]/80 transition-colors"
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Edit Modal */}
            {isEditing && selectedDoc && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-[var(--bg-dark-2)] rounded-xl border border-[var(--border-color)] max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-[var(--border-color)] flex justify-between items-center">
                            <h2 className="text-2xl font-bold text-[var(--green-dark)]">Edit Document</h2>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="text-[var(--text-muted)] hover:text-[var(--text-light)] text-2xl"
                            >
                                ×
                            </button>
                        </div>

                        {/* Edit Modal */}
                        {isEditing && selectedDoc && (
                            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                                <div className="bg-[var(--bg-dark-2)] rounded-2xl border border-[var(--border-color)] w-full max-w-6xl h-[90vh] flex flex-col">
                                    {/* Header */}
                                    <div className="p-6 border-b border-[var(--border-color)] flex justify-between items-center">
                                        <div className="flex items-center gap-4">
                                            <h2 className="text-2xl font-bold text-[var(--green-dark)]">
                                                Edit Document: {selectedDoc._id}
                                            </h2>
                                            <div className="flex items-center gap-2">
                                                {isValidJson ? (
                                                    <span className="flex items-center gap-2 text-green-400">
                                                        <CheckCircle className="w-5 h-5" /> Valid JSON
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-2 text-red-400">
                                                        <XCircle className="w-5 h-5" /> Invalid JSON
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={() => setShowDiff(!showDiff)}
                                                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${showDiff
                                                    ? "bg-[var(--green-dark)] text-white"
                                                    : "bg-[var(--bg-dark-3)] hover:bg-[var(--bg-dark-3)]/80"
                                                    }`}
                                            >
                                                <GitCompare className="w-5 h-5" />
                                                Diff View
                                            </button>
                                            <button
                                                onClick={handleSave}
                                                disabled={!isValidJson || updateMutation.isPending}
                                                className="bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all"
                                            >
                                                {updateMutation.isPending ? (
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                ) : (
                                                    <Save className="w-5 h-5" />
                                                )}
                                                Save
                                            </button>
                                            <button
                                                onClick={() => setIsEditing(false)}
                                                className="text-[var(--text-muted)] hover:text-[var(--text-light)] text-3xl"
                                            >
                                                ×
                                            </button>
                                        </div>
                                    </div>

                                    {/* Editor */}
                                    <div className="flex-1 flex overflow-hidden">
                                        {/* Original (Diff View) */}
                                        {/* Current Editor - _id is read-only */}
                                        <div className={showDiff ? "w-1/2 p-4" : "w-full p-4"}>
                                            <h3 className="text-sm font-semibold text-[var(--text-muted)] mb-2">
                                                {showDiff ? "New Document" : "Current"}
                                            </h3>
                                            <div className="h-full flex flex-col">
                                                {/* Read-only _id field */}
                                                <div className="mb-4 p-4 bg-[var(--bg-dark-3)] rounded-lg border border-[var(--border-color)]">
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <span className="text-sm text-[var(--text-muted)]">Document ID (_id)</span>
                                                            <div className="flex items-center gap-3 mt-2">
                                                                <code className="font-mono text-sm text-[var(--text-light)] break-all">
                                                                    {selectedDoc?._id}
                                                                </code>
                                                                <button
                                                                    onClick={() => {
                                                                        navigator.clipboard.writeText(selectedDoc?._id || "");
                                                                        toast.success("ID copied!");
                                                                    }}
                                                                    className="text-[var(--text-muted)] hover:text-[var(--green-dark)]"
                                                                >
                                                                    <Copy className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        </div>
                                                        <span className="text-xs text-[var(--text-muted)] bg-[var(--bg-dark-1)] px-3 py-1 rounded-full">
                                                            Read-only
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Editable JSON (without _id) */}
                                                <div className="flex-1 bg-[var(--bg-dark-1)] rounded-lg border border-[var(--border-color)] overflow-hidden">
                                                    <Editor
                                                        height="100%"
                                                        defaultLanguage="json"
                                                        value={JSON.stringify(
                                                            Object.fromEntries(
                                                                Object.entries(selectedDoc || {}).filter(([key]) => key !== "_id")
                                                            ),
                                                            null,
                                                            2
                                                        )}
                                                        onChange={handleEditorChange}
                                                        onMount={handleEditorDidMount}
                                                        theme="datacube-dark"
                                                        options={{
                                                            minimap: { enabled: false },
                                                            scrollBeyondLastLine: false,
                                                            fontSize: 14,
                                                            wordWrap: "on",
                                                            automaticLayout: true,
                                                            folding: true,
                                                            renderValidationDecorations: "on",
                                                            readOnly: false,
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Current */}
                                        {showDiff && (
                                        <div className={showDiff ? "w-1/2 p-4" : "w-full p-4"}>
                                            <h3 className="text-sm font-semibold text-[var(--text-muted)] mb-2">
                                                Current
                                            </h3>
                                            <Editor
                                                height="100%"
                                                defaultLanguage="json"
                                                value={JSON.stringify(
                                                    Object.fromEntries(
                                                        Object.entries(selectedDoc || {}).filter(([key]) => key !== "_id")
                                                    ),
                                                    null,
                                                    2
                                                )}
                                                // onChange={handleEditorChange}
                                                onMount={handleEditorDidMount}
                                                theme="datacube-dark"
                                                options={{
                                                    minimap: { enabled: false },
                                                    scrollBeyondLastLine: false,
                                                    fontSize: 14,
                                                    wordWrap: "on",
                                                    automaticLayout: true,
                                                    folding: true,
                                                    renderValidationDecorations: "on",
                                                }}
                                            />
                                        </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                        <div className="p-6 border-t border-[var(--border-color)] flex justify-end gap-4">
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-6 py-3 rounded-lg bg-[var(--bg-dark-3)] hover:bg-[var(--bg-dark-3)]/80 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleSave()}
                                disabled={updateMutation.isPending}
                                className="px-8 py-3 rounded-lg bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 text-white font-semibold transition-all flex items-center gap-2"
                            >
                                {updateMutation.isPending ? (
                                    <>Saving...</>
                                ) : (
                                    <>Save Document</>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CollectionDocuments;