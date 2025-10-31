"use client";

import { Paper, paperApi, QueryResult } from "@/lib/api";
import { AlertCircle, BookOpen, FileText, Loader2, Search } from "lucide-react";
import { useEffect, useState } from "react";

export default function QueryInterface() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaperIds, setSelectedPaperIds] = useState<number[]>([]);
  const [loadingPapers, setLoadingPapers] = useState(false);

  // Load papers on mount
  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = async () => {
    setLoadingPapers(true);
    try {
      const data = await paperApi.listPapers();
      setPapers(data.papers);
    } catch (err: any) {
      console.error("Load papers error:", err);
    } finally {
      setLoadingPapers(false);
    }
  };

  const handlePaperToggle = (paperId: number) => {
    setSelectedPaperIds((prev) =>
      prev.includes(paperId)
        ? prev.filter((id) => id !== paperId)
        : [...prev, paperId]
    );
  };

  const handleSelectAll = () => {
    if (selectedPaperIds.length === papers.length) {
      setSelectedPaperIds([]);
    } else {
      setSelectedPaperIds(papers.map((p) => p.id));
    }
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setError("Please enter a question before searching.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      // Only pass paper_ids if some are selected (not all or none)
      const paperIdsToSend =
        selectedPaperIds.length > 0 && selectedPaperIds.length < papers.length
          ? selectedPaperIds
          : undefined;

      const data = await paperApi.query(query, topK, paperIdsToSend);
      setResult(data);
    } catch (err: any) {
      console.error("Query error:", err);

      // Enhanced error handling with safe string extraction
      if (err.response?.status === 404) {
        setError(
          "No papers found in the database. Please upload some papers first."
        );
      } else if (err.response?.status === 500) {
        setError(
          "Server error while processing your query. Please try again or simplify your question."
        );
      } else if (
        err.code === "ECONNREFUSED" ||
        err.message?.includes("Network Error")
      ) {
        setError(
          "Cannot connect to the server. Please ensure the backend is running."
        );
      } else if (err.response?.status === 400) {
        const detail = err.response?.data?.detail;
        setError(
          typeof detail === "string"
            ? detail
            : "Invalid query format. Please rephrase your question."
        );
      } else {
        const detail = err.response?.data?.detail;
        const message = err.response?.data?.message;
        const errMessage = err.message;

        let errorText = "Failed to query papers. Please try again.";
        if (typeof detail === "string") {
          errorText = detail;
        } else if (typeof message === "string") {
          errorText = message;
        } else if (typeof errMessage === "string") {
          errorText = errMessage;
        }

        setError(errorText);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="border-b border-slate-300 pb-3">
        <h2 className="text-xl font-bold text-slate-900 mb-1">
          Ask a Question
        </h2>
        <p className="text-xs text-slate-600">
          Query your uploaded research papers and get AI-powered answers with
          citations.
        </p>
      </div>

      {/* Query Form */}
      <form onSubmit={handleQuery} className="space-y-3">
        <div className="bg-white rounded-lg border border-slate-300 p-4 shadow-sm">
          <label
            htmlFor="query"
            className="block text-xs font-bold text-slate-800 mb-2 uppercase tracking-wide"
          >
            Research Question
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What methodology was used in the transformer paper?"
            rows={3}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-slate-900 placeholder-slate-400 text-sm leading-relaxed"
          />
        </div>

        {/* Paper Selection Filter */}
        {papers.length > 0 && (
          <div className="bg-white rounded-lg border border-slate-300 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide">
                Filter by Papers
                {selectedPaperIds.length > 0 &&
                  selectedPaperIds.length < papers.length && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-blue-600 text-white">
                      {selectedPaperIds.length}
                    </span>
                  )}
              </label>
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-xs text-blue-700 hover:text-blue-800 font-bold uppercase tracking-wide"
              >
                {selectedPaperIds.length === papers.length
                  ? "Clear"
                  : "Select All"}
              </button>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2">
              {loadingPapers ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 size={20} className="text-blue-600 animate-spin" />
                </div>
              ) : (
                papers.map((paper) => (
                  <label
                    key={paper.id}
                    className="flex items-start space-x-2.5 p-2.5 rounded-md hover:bg-slate-100 cursor-pointer transition-colors border border-transparent hover:border-slate-200"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPaperIds.includes(paper.id)}
                      onChange={() => handlePaperToggle(paper.id)}
                      className="mt-0.5 w-4 h-4 text-blue-600 rounded border-slate-400 focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 leading-tight truncate">
                        {paper.title || paper.filename}
                      </p>
                      {paper.author && (
                        <p className="text-xs text-slate-600 mt-0.5 leading-tight">
                          {paper.author}
                        </p>
                      )}
                      <p className="text-xs text-slate-500 mt-1 font-medium">
                        {paper.page_count} pages • {paper.total_chunks} chunks
                      </p>
                    </div>
                  </label>
                ))
              )}
            </div>
            <p className="text-xs text-slate-600 mt-2.5 font-medium">
              {selectedPaperIds.length === 0 ||
              selectedPaperIds.length === papers.length
                ? "🔍 Searching across all papers"
                : `🎯 Searching in ${selectedPaperIds.length} selected paper${
                    selectedPaperIds.length > 1 ? "s" : ""
                  }`}
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white rounded-lg border border-slate-300 p-3 shadow-sm">
            <label
              htmlFor="topK"
              className="block text-xs font-bold text-slate-800 mb-2 uppercase tracking-wide"
            >
              Chunks: <span className="text-blue-600">{topK}</span>
            </label>
            <input
              id="topK"
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1 font-medium">
              <span>1</span>
              <span>20+</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all font-bold shadow-md hover:shadow-lg text-sm uppercase tracking-wide"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Searching</span>
              </>
            ) : (
              <>
                <Search size={18} />
                <span>Search</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg flex items-start space-x-2.5 animate-fadeIn">
          <AlertCircle
            className="text-red-700 flex-shrink-0 mt-0.5"
            size={18}
          />
          <div className="flex-1">
            <h4 className="font-bold text-red-900 mb-0.5 text-xs uppercase tracking-wide">
              Query Failed
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

      {/* Results */}
      {result && (
        <div className="space-y-3">
          {/* Answer Card */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100/70 rounded-lg border-2 border-blue-300 p-4 shadow-md">
            <div className="flex items-start space-x-2.5 mb-3">
              <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                <BookOpen className="text-white" size={18} />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-slate-900 mb-2 uppercase tracking-wide">
                  Answer
                </h3>
                <p className="text-slate-800 leading-relaxed whitespace-pre-wrap text-sm font-medium">
                  {result.answer}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-700 pt-3 border-t-2 border-blue-200 font-bold">
              <span>
                Response:{" "}
                <span className="text-blue-700">{result.response_time}s</span>
              </span>
              {result.confidence && (
                <span>
                  Confidence:{" "}
                  <span className="text-blue-700">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                </span>
              )}
            </div>
          </div>

          {/* Citations */}
          {result.citations && result.citations.length > 0 && (
            <div>
              <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center uppercase tracking-wide">
                <FileText className="mr-2 text-slate-700" size={18} />
                Source Citations ({result.citations.length})
              </h3>
              <div className="space-y-2">
                {result.citations.map((citation, index) => (
                  <div
                    key={index}
                    className="bg-white border-2 border-slate-300 rounded-lg p-3 shadow-sm hover:shadow-md hover:border-slate-400 transition-all"
                  >
                    <div className="flex items-start justify-between mb-1.5">
                      <h4 className="font-bold text-slate-900 text-sm flex-1 leading-tight">
                        {citation.paper_title}
                      </h4>
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded font-bold ml-2 uppercase tracking-wide shadow-sm">
                        P.{citation.page_number}
                      </span>
                    </div>
                    {citation.section && (
                      <p className="text-xs text-slate-700 mb-1.5 font-semibold">
                        Section: {citation.section}
                      </p>
                    )}
                    <p className="text-sm text-slate-700 italic leading-relaxed font-medium">
                      "{citation.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
