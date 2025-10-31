"use client";

import { paperApi, QueryHistory } from "@/lib/api";
import { format } from "date-fns";
import {
  AlertCircle,
  BookOpen,
  Clock,
  History,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { useEffect, useState } from "react";

export default function QueryHistoryView() {
  const [queries, setQueries] = useState<QueryHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedQuery, setSelectedQuery] = useState<QueryHistory | null>(null);
  const [error, setError] = useState("");

  const loadHistory = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await paperApi.getQueryHistory(50);
      setQueries(data.queries);
    } catch (err: any) {
      console.error("Load history error:", err);

      if (
        err.code === "ECONNREFUSED" ||
        err.message?.includes("Network Error")
      ) {
        setError(
          "Cannot connect to the server. Please ensure the backend is running."
        );
      } else if (err.response?.status === 500) {
        setError("Server error while loading query history. Please try again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Failed to load query history. Please try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900 mb-1">
            Query History
          </h2>
          <p className="text-sm text-slate-600">
            View your previous queries and their responses.
          </p>
        </div>
        <button
          onClick={loadHistory}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 disabled:bg-slate-100 transition-all card-shadow hover:card-shadow-hover"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          <span className="text-sm font-medium">Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3 animate-fadeIn">
          <AlertCircle
            className="text-red-600 flex-shrink-0 mt-0.5"
            size={20}
          />
          <div className="flex-1">
            <h4 className="font-semibold text-red-800 mb-1 text-sm">Error</h4>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
          <button
            onClick={() => setError("")}
            className="text-red-400 hover:text-red-600 transition-colors"
          >
            ✕
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={40} className="text-blue-600 animate-spin" />
        </div>
      ) : queries.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200 card-shadow">
          <History size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-600 text-sm">
            No query history yet. Start asking questions to see them here!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-1 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">
              Recent Queries ({queries.length})
            </h3>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
              {queries.map((query) => (
                <div
                  key={query.id}
                  className={`p-3 border rounded-lg transition-all cursor-pointer card-shadow hover:card-shadow-hover ${
                    selectedQuery?.id === query.id
                      ? "border-blue-500 ring-2 ring-blue-100 bg-blue-50"
                      : "border-slate-200 bg-white"
                  }`}
                  onClick={() => setSelectedQuery(query)}
                >
                  <p className="font-medium text-slate-900 mb-2 line-clamp-2 text-sm">
                    {query.query_text}
                  </p>
                  <div className="flex items-center flex-wrap gap-2 text-xs text-slate-500">
                    <span className="flex items-center">
                      <Clock size={12} className="mr-1" />
                      {format(new Date(query.created_at), "MMM d")}
                    </span>
                    <span className="flex items-center">
                      <BookOpen size={12} className="mr-1" />
                      {query.papers_referenced.length} papers
                    </span>
                    <span>{query.response_time.toFixed(1)}s</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2">
            {selectedQuery ? (
              <div className="bg-white border border-slate-200 rounded-xl p-6 card-shadow">
                <h3 className="text-lg font-semibold text-slate-900 mb-4 pb-3 border-b border-slate-200">
                  Query Details
                </h3>

                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                      Question
                    </h4>
                    <p className="text-slate-900 font-medium text-sm">
                      {selectedQuery.query_text}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 p-4 rounded-lg">
                    <h4 className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                      Answer
                    </h4>
                    <p className="text-slate-700 leading-relaxed whitespace-pre-wrap text-sm">
                      {selectedQuery.answer}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <p className="text-xs text-slate-600 mb-1">
                        Response Time
                      </p>
                      <p className="font-medium text-slate-900 text-sm">
                        {selectedQuery.response_time.toFixed(2)}s
                      </p>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <p className="text-xs text-slate-600 mb-1">Timestamp</p>
                      <p className="font-medium text-slate-900 text-sm">
                        {format(
                          new Date(selectedQuery.created_at),
                          "MMM d, h:mm a"
                        )}
                      </p>
                    </div>
                  </div>

                  {selectedQuery.papers_referenced.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                        Papers Referenced (
                        {selectedQuery.papers_referenced.length})
                      </h4>
                      <div className="space-y-2">
                        {selectedQuery.papers_referenced.map((paper, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-slate-50 rounded-lg border border-slate-100"
                          >
                            <p className="text-sm text-slate-900">{paper}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 bg-white border-2 border-dashed border-slate-200 rounded-xl">
                <p className="text-slate-500 text-sm">
                  Select a query to view details
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
