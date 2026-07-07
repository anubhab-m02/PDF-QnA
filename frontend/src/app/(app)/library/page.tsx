"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileText } from "lucide-react";
import { toast } from "sonner";
import { UploadDropzone } from "@/components/library/upload-dropzone";
import { DocumentCard } from "@/components/library/document-card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, authHeaders, ApiError, NetworkError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Document } from "@/lib/documents";

const POLL_INTERVAL_MS = 2500;

export default function LibraryPage() {
  const { token } = useAuth();
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    try {
      const docs = await apiFetch<Document[]>("/api/documents", { headers: authHeaders(token) });
      setDocuments(docs);
    } catch (err) {
      if (err instanceof NetworkError) toast.error(err.message);
    }
  }, [token]);

  useEffect(() => {
    // Initial fetch on mount — synchronizing with the server, not derivable from props/state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    const anyProcessing = documents?.some((d) => d.status === "processing") ?? false;

    if (anyProcessing && !intervalRef.current) {
      intervalRef.current = setInterval(fetchDocuments, POLL_INTERVAL_MS);
    }
    if (!anyProcessing && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [documents, fetchDocuments]);

  async function handleUpload(file: File) {
    if (!token) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const doc = await apiFetch<Document>("/api/documents", {
        method: "POST",
        headers: authHeaders(token),
        body: formData,
      });
      setDocuments((prev) => [doc, ...(prev ?? [])]);
    } catch (err) {
      if (err instanceof ApiError || err instanceof NetworkError) {
        toast.error(err.message);
      } else {
        toast.error("Upload failed. Please try again.");
      }
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!token) return;
    try {
      await apiFetch(`/api/documents/${id}`, { method: "DELETE", headers: authHeaders(token) });
      setDocuments((prev) => (prev ?? []).filter((d) => d.id !== id));
      toast.success("Document deleted");
    } catch (err) {
      if (err instanceof ApiError || err instanceof NetworkError) {
        toast.error(err.message);
      } else {
        toast.error("Failed to delete document");
      }
    }
  }

  const isEmpty = documents !== null && documents.length === 0;

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-8">
        <UploadDropzone onFileSelected={handleUpload} />

        {uploading && (
          <p className="text-sm text-muted-foreground">Uploading…</p>
        )}

        {documents === null && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-lg" />
            ))}
          </div>
        )}

        {isEmpty && (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <FileText className="size-10 text-muted-foreground" />
            <p className="text-lg font-medium">No documents yet</p>
            <p className="text-sm text-muted-foreground">Upload a PDF to start learning</p>
          </div>
        )}

        {documents && documents.length > 0 && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
            {documents.map((doc) => (
              <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
