"use client";

import { paperApi } from "@/lib/api";
import {
  AlertCircle,
  CheckCircle,
  FileText,
  Loader2,
  Upload,
  X,
} from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface UploadResult {
  file: string;
  status: "success" | "error" | "duplicate";
  message?: string;
  data?: any;
}

export default function UploadPaper() {
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [currentFile, setCurrentFile] = useState<string>("");
  const [error, setError] = useState("");

  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: any[]) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const rejectionMessages = rejectedFiles.map((rejection) => {
          if (rejection.errors[0]?.code === "file-invalid-type") {
            return `${rejection.file.name}: Invalid file type (PDF only)`;
          } else if (rejection.errors[0]?.code === "file-too-large") {
            return `${rejection.file.name}: File too large (Max 50MB)`;
          } else {
            return `${rejection.file.name}: File rejected`;
          }
        });
        setError(rejectionMessages.join(", "));
        return;
      }

      if (acceptedFiles.length === 0) return;

      setUploading(true);
      setError("");
      setResults([]);
      setCurrentFile(
        acceptedFiles.length > 1
          ? `${acceptedFiles.length} files`
          : acceptedFiles[0].name
      );

      try {
        // Use single endpoint for both single and multiple files
        const data = await paperApi.uploadPaper(
          acceptedFiles.length === 1 ? acceptedFiles[0] : acceptedFiles
        );

        // Handle response - could be single result or batch results
        let uploadResults: UploadResult[];

        if (data.status === "completed") {
          // Multiple files response
          uploadResults = data.results.map((result: any) => ({
            file: result.filename,
            status:
              result.status === "success"
                ? "success"
                : result.status === "error" &&
                  result.message?.includes("already exists")
                ? "duplicate"
                : "error",
            message:
              typeof result.message === "string"
                ? result.message
                : result.message
                ? JSON.stringify(result.message)
                : undefined,
            data: result.status === "success" ? result : undefined,
          }));
        } else {
          // Single file response
          uploadResults = [
            {
              file: acceptedFiles[0].name,
              status:
                data.status === "success"
                  ? "success"
                  : data.status === "error" &&
                    data.message?.includes("already exists")
                  ? "duplicate"
                  : "error",
              message:
                typeof data.message === "string"
                  ? data.message
                  : data.message
                  ? JSON.stringify(data.message)
                  : undefined,
              data: data.status === "success" ? data : undefined,
            },
          ];
        }

        setResults(uploadResults);
      } catch (err: any) {
        console.error("Upload error:", err);

        // Log the full error response for debugging
        if (err.response?.data) {
          console.error("Error response data:", err.response.data);
        }

        let errorMessage = "Failed to upload";

        // Handle different error types
        if (err.response?.status === 422) {
          // Unprocessable Entity - validation error
          const detail = err.response?.data?.detail;
          if (Array.isArray(detail)) {
            errorMessage = detail
              .map((e: any) => {
                const field = e.loc?.join(".") || "field";
                const msg = e.msg || "validation error";
                return `${field}: ${msg}`;
              })
              .join(", ");
          } else if (typeof detail === "string") {
            errorMessage = detail;
          } else {
            errorMessage = "Invalid request format";
          }
        } else if (err.response?.status === 413) {
          errorMessage = "File too large (Max 50MB)";
        } else if (err.response?.status === 415) {
          errorMessage = "Unsupported file type";
        } else if (err.response?.status === 400) {
          // Handle validation errors that might be objects
          const detail = err.response?.data?.detail;
          if (typeof detail === "string") {
            errorMessage = detail;
          } else if (Array.isArray(detail)) {
            errorMessage = detail
              .map((e: any) =>
                typeof e === "string" ? e : e.msg || "Invalid format"
              )
              .join(", ");
          } else if (detail && typeof detail === "object") {
            errorMessage = detail.msg || JSON.stringify(detail);
          } else {
            errorMessage = "Invalid file format";
          }
        } else if (err.response?.status === 500) {
          errorMessage = "Server error";
        } else if (
          err.code === "ECONNREFUSED" ||
          err.message?.includes("Network Error")
        ) {
          errorMessage = "Cannot connect to server";
        } else {
          // Safely extract error message
          const detail = err.response?.data?.detail;
          const message = err.response?.data?.message;

          if (typeof detail === "string") {
            errorMessage = detail;
          } else if (typeof message === "string") {
            errorMessage = message;
          } else if (typeof err.message === "string") {
            errorMessage = err.message;
          } else {
            errorMessage = "Upload failed";
          }
        }

        setError(errorMessage);
      } finally {
        setCurrentFile("");
        setUploading(false);
      }
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    multiple: true,
    maxSize: 52428800, // 50MB in bytes
    disabled: uploading,
  });

  const successCount = results.filter((r) => r.status === "success").length;
  const duplicateCount = results.filter((r) => r.status === "duplicate").length;
  const errorCount = results.filter((r) => r.status === "error").length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="border-b border-slate-300 pb-3">
        <h2 className="text-xl font-bold text-slate-900 mb-1">Upload Papers</h2>
        <p className="text-xs text-slate-600">
          Upload PDF research papers to add them to your knowledge base.
          Multiple files supported.
        </p>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all ${
          isDragActive
            ? "border-blue-500 bg-blue-50"
            : "border-slate-400 hover:border-blue-500 hover:bg-slate-50"
        } ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-3">
          {uploading ? (
            <>
              <Loader2 size={40} className="text-blue-600 animate-spin" />
              <p className="text-base font-bold text-slate-800 uppercase tracking-wide">
                Processing Papers...
              </p>
              <p className="text-xs text-slate-600 font-medium">
                Currently uploading:{" "}
                <span className="text-blue-600">{currentFile}</span>
              </p>
            </>
          ) : (
            <>
              <div className="w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center shadow-md">
                <Upload size={28} className="text-white" />
              </div>
              {isDragActive ? (
                <p className="text-base font-bold text-blue-600 uppercase tracking-wide">
                  Drop PDF files here...
                </p>
              ) : (
                <>
                  <p className="text-base font-bold text-slate-900 uppercase tracking-wide">
                    Drag & Drop PDFs or Click to Select
                  </p>
                  <p className="text-xs text-slate-600 font-medium">
                    Multiple files supported • PDF only • Max 50MB each
                  </p>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg flex items-start space-x-2.5 animate-fadeIn">
          <AlertCircle
            className="text-red-700 flex-shrink-0 mt-0.5"
            size={18}
          />
          <div className="flex-1">
            <h4 className="font-bold text-red-900 mb-0.5 text-xs uppercase tracking-wide">
              Upload Failed
            </h4>
            <p className="text-red-800 text-sm font-medium">{error}</p>
          </div>
          <button
            onClick={() => setError("")}
            className="text-red-500 hover:text-red-700 transition-colors font-bold"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Upload Results Summary */}
      {results.length > 0 && (
        <div className="space-y-3">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-3">
            {successCount > 0 && (
              <div className="bg-green-50 border-2 border-green-300 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-700">
                  {successCount}
                </p>
                <p className="text-xs font-bold text-green-800 uppercase tracking-wide">
                  Successful
                </p>
              </div>
            )}
            {duplicateCount > 0 && (
              <div className="bg-amber-50 border-2 border-amber-300 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-amber-700">
                  {duplicateCount}
                </p>
                <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                  Duplicates
                </p>
              </div>
            )}
            {errorCount > 0 && (
              <div className="bg-red-50 border-2 border-red-300 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-red-700">{errorCount}</p>
                <p className="text-xs font-bold text-red-800 uppercase tracking-wide">
                  Failed
                </p>
              </div>
            )}
          </div>

          {/* Individual Results */}
          <div className="space-y-2">
            {results.map((result, index) => (
              <div
                key={index}
                className={`rounded-lg p-3 border-2 ${
                  result.status === "success"
                    ? "bg-green-50 border-green-300"
                    : result.status === "duplicate"
                    ? "bg-amber-50 border-amber-300"
                    : "bg-red-50 border-red-300"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-2.5 flex-1">
                    {result.status === "success" ? (
                      <CheckCircle
                        className="text-green-700 flex-shrink-0 mt-0.5"
                        size={18}
                      />
                    ) : (
                      <AlertCircle
                        className={`flex-shrink-0 mt-0.5 ${
                          result.status === "duplicate"
                            ? "text-amber-700"
                            : "text-red-700"
                        }`}
                        size={18}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <FileText
                          size={14}
                          className="text-slate-600 flex-shrink-0"
                        />
                        <p className="text-sm font-bold text-slate-900 truncate">
                          {result.file}
                        </p>
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded uppercase tracking-wide ${
                            result.status === "success"
                              ? "bg-green-600 text-white"
                              : result.status === "duplicate"
                              ? "bg-amber-600 text-white"
                              : "bg-red-600 text-white"
                          }`}
                        >
                          {result.status}
                        </span>
                      </div>

                      {result.message && typeof result.message === "string" && (
                        <p className="text-xs font-medium text-slate-700 mt-1">
                          {result.message}
                        </p>
                      )}

                      {result.status === "success" && result.data && (
                        <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-2">
                          {result.data.metadata?.title && (
                            <div className="bg-white rounded border border-green-200 p-2">
                              <p className="text-xs text-slate-600 font-bold uppercase tracking-wide">
                                Title
                              </p>
                              <p className="text-xs font-semibold text-slate-900 truncate">
                                {result.data.metadata.title}
                              </p>
                            </div>
                          )}
                          {result.data.metadata?.author && (
                            <div className="bg-white rounded border border-green-200 p-2">
                              <p className="text-xs text-slate-600 font-bold uppercase tracking-wide">
                                Author
                              </p>
                              <p className="text-xs font-semibold text-slate-900 truncate">
                                {result.data.metadata.author}
                              </p>
                            </div>
                          )}
                          <div className="bg-white rounded border border-green-200 p-2">
                            <p className="text-xs text-slate-600 font-bold uppercase tracking-wide">
                              Chunks
                            </p>
                            <p className="text-xs font-bold text-blue-700">
                              {result.data.total_chunks}
                            </p>
                          </div>
                          <div className="bg-white rounded border border-green-200 p-2">
                            <p className="text-xs text-slate-600 font-bold uppercase tracking-wide">
                              ID
                            </p>
                            <p className="text-xs font-bold text-blue-700">
                              {result.data.paper_id}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
