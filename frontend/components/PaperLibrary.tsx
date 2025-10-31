"use client";

import { Paper, paperApi } from "@/lib/api";
import { format } from "date-fns";
import {
  AlertCircle,
  BookOpen,
  Calendar,
  FileText,
  Loader2,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import Toast from "./Toast";

export default function PaperLibrary() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "warning" | "info";
  } | null>(null);

  const loadPapers = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await paperApi.listPapers();
      setPapers(data.papers);
    } catch (err: any) {
      console.error("Load papers error:", err);

      if (
        err.code === "ECONNREFUSED" ||
        err.message?.includes("Network Error")
      ) {
        setError(
          "Cannot connect to the server. Please ensure the backend is running."
        );
      } else if (err.response?.status === 500) {
        setError("Server error while loading papers. Please try again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Failed to load papers. Please try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPapers();
  }, []);

  const handleDelete = async (paperId: number) => {
    if (
      !confirm(
        "Are you sure you want to delete this paper? This action cannot be undone."
      )
    )
      return;

    try {
      await paperApi.deletePaper(paperId);
      setPapers(papers.filter((p) => p.id !== paperId));
      if (selectedPaper?.id === paperId) {
        setSelectedPaper(null);
      }
      // Show success toast
      setError("");
      setToast({ message: "Paper deleted successfully!", type: "success" });
    } catch (err: any) {
      console.error("Delete paper error:", err);

      if (err.response?.status === 404) {
        setError("Paper not found. It may have already been deleted.");
        // Refresh the list
        loadPapers();
      } else if (err.response?.status === 500) {
        setError("Server error while deleting paper. Please try again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Failed to delete paper. Please try again."
        );
      }
    }
  };

  const handleViewDetails = async (paper: Paper) => {
    try {
      const fullPaper = await paperApi.getPaper(paper.id);
      setSelectedPaper(fullPaper);
      setError("");
    } catch (err: any) {
      console.error("Load paper details error:", err);

      if (err.response?.status === 404) {
        setError("Paper not found. It may have been deleted.");
        loadPapers();
      } else {
        setError("Failed to load paper details. Please try again.");
      }
    }
  };

  return (
    <div className="space-y-4">
      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-300 pb-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-1">My Papers</h2>
          <p className="text-xs text-slate-600">
            Browse and manage your uploaded research papers.
          </p>
        </div>
        <button
          onClick={loadPapers}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white border-2 border-slate-300 text-slate-800 rounded-lg hover:bg-slate-50 hover:border-slate-400 disabled:bg-slate-100 transition-all shadow-sm font-bold text-xs uppercase tracking-wide"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg flex items-start space-x-2.5 animate-fadeIn">
          <AlertCircle
            className="text-red-700 flex-shrink-0 mt-0.5"
            size={18}
          />
          <div className="flex-1">
            <h4 className="font-bold text-red-900 mb-0.5 text-xs uppercase tracking-wide">
              Error
            </h4>
            <p className="text-red-800 text-sm font-medium">{error}</p>
          </div>
          <button
            onClick={() => setError("")}
            className="text-red-500 hover:text-red-700 transition-colors font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={36} className="text-blue-600 animate-spin" />
        </div>
      ) : papers.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-slate-300">
          <BookOpen size={40} className="mx-auto text-slate-400 mb-3" />
          <p className="text-slate-700 text-sm font-medium">
            No papers uploaded yet. Upload your first paper to get started!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className={`bg-white border-2 rounded-lg p-4 transition-all cursor-pointer shadow-sm hover:shadow-md ${
                selectedPaper?.id === paper.id
                  ? "border-blue-600 ring-2 ring-blue-100"
                  : "border-slate-300 hover:border-slate-400"
              }`}
              onClick={() => handleViewDetails(paper)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                  <FileText className="text-white" size={18} />
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(paper.id);
                    }}
                    className="p-1.5 text-slate-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                    title="Delete paper"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>

              <h4 className="font-bold text-slate-900 mb-1 text-sm line-clamp-2 leading-tight">
                {paper.title || paper.filename}
              </h4>

              {paper.author && (
                <p className="text-xs text-slate-600 mb-2.5 font-medium">
                  by {paper.author}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-slate-600 pt-2.5 border-t-2 border-slate-200 font-medium">
                <span className="flex items-center">
                  <FileText size={12} className="mr-1" />
                  {paper.page_count} pages
                </span>
                <span className="flex items-center">
                  <Calendar size={12} className="mr-1" />
                  {format(new Date(paper.upload_date), "MMM d")}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Paper Details Panel */}
      {selectedPaper && (
        <div className="bg-white border-2 border-slate-300 rounded-lg p-5 shadow-md">
          <h3 className="text-base font-bold text-slate-900 mb-3 pb-3 border-b-2 border-slate-300 uppercase tracking-wide">
            Paper Details
          </h3>

          <div className="space-y-3">
            <div>
              <h4 className="text-lg font-bold text-slate-900 mb-1 leading-tight">
                {selectedPaper.title || selectedPaper.filename}
              </h4>
              {selectedPaper.author && (
                <p className="text-slate-700 text-sm font-semibold">
                  by {selectedPaper.author}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3">
              <div className="bg-slate-100 p-2.5 rounded border border-slate-300">
                <p className="text-xs text-slate-700 mb-0.5 font-bold uppercase tracking-wide">
                  Filename
                </p>
                <p className="font-semibold text-slate-900 text-xs truncate">
                  {selectedPaper.filename}
                </p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">Pages</p>
                <p className="font-medium text-slate-900 text-sm">
                  {selectedPaper.page_count}
                </p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">Chunks</p>
                <p className="font-medium text-slate-900 text-sm">
                  {selectedPaper.total_chunks}
                </p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">Uploaded</p>
                <p className="font-medium text-slate-900 text-sm">
                  {format(new Date(selectedPaper.upload_date), "MMM d, yyyy")}
                </p>
              </div>
            </div>

            {selectedPaper.sections &&
              Object.keys(selectedPaper.sections).length > 0 && (
                <div className="pt-4">
                  <h5 className="font-semibold text-slate-900 mb-3 text-sm">
                    Sections ({Object.keys(selectedPaper.sections).length})
                  </h5>
                  <div className="space-y-2">
                    {Object.entries(selectedPaper.sections).map(
                      ([section, data]: [string, any]) => (
                        <div
                          key={section}
                          className="p-3 bg-slate-50 rounded-lg border border-slate-100"
                        >
                          <p className="font-medium text-slate-900 text-sm">
                            {section}
                          </p>
                          <p className="text-xs text-slate-600 mt-1">
                            {data.chunk_count} chunks • Page {data.start_page}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
          </div>
        </div>
      )}
    </div>
  );
}
