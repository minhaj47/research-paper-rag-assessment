"use client";

import PaperLibrary from "@/components/PaperLibrary";
import QueryHistoryView from "@/components/QueryHistoryView";
import QueryInterface from "@/components/QueryInterface";
import UploadPaper from "@/components/UploadPaper";
import { Database, History, Search, Upload } from "lucide-react";
import { useState } from "react";

type Tab = "query" | "library" | "upload" | "history";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("query");

  const tabs = [
    { id: "query" as Tab, label: "Query Papers", icon: Search },
    { id: "upload" as Tab, label: "Upload Papers", icon: Upload },
    { id: "library" as Tab, label: "My Papers", icon: Database },
    { id: "history" as Tab, label: "Query History", icon: History },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <Search className="text-white" size={18} />
              </div>
              <h1 className="text-xl font-semibold text-slate-900">
                Research Paper Assistant
              </h1>
            </div>

            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-slate-600 font-medium">
                System Online
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Left Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 p-4">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all text-left ${
                    activeTab === tab.id
                      ? "bg-blue-50 text-blue-700 font-medium shadow-sm"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <Icon
                    size={20}
                    className={
                      activeTab === tab.id ? "text-blue-600" : "text-slate-400"
                    }
                  />
                  <span className="text-sm">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <div className="max-w-5xl">
            {activeTab === "query" && <QueryInterface />}
            {activeTab === "library" && <PaperLibrary />}
            {activeTab === "upload" && <UploadPaper />}
            {activeTab === "history" && <QueryHistoryView />}
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <p className="text-center text-sm text-slate-500">
            Built with{" "}
            <span className="font-medium text-slate-700">
              Next.js, FastAPI, Qdrant & Ollama
            </span>
          </p>
        </div>
      </footer>
    </div>
  );
}
