"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  FileText, 
  UploadCloud, 
  Search, 
  Sparkles, 
  Cpu, 
  CheckCircle2, 
  AlertCircle, 
  FolderHeart,
  Layers,
  User,
  Bot,
  LogOut,
  LogIn,
  Eye,
  X,
  BookOpen,
  Zap
} from "lucide-react";
import { 
  uploadPhysicalFile, 
  fetchUserFiles, 
  fetchChatHistory, 
  streamAgenticRag,
  fetchCurrentUser,
  clearAuthToken,
  TrackedFile, 
  ChatMessage, 
  SourceChunk,
  AuthUser 
} from "./services/api";
import AuthModal from "./components/AuthModal";

export default function ContextIqDashboard() {
  // Auth state
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  // Vault and network data managers
  const [uploadedFiles, setUploadedFiles] = useState<TrackedFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<TrackedFile | null>(null);
  const [activeHistory, setActiveHistory] = useState<ChatMessage[]>([]);
  
  // Async status states
  const [uploadLoading, setUploadLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  
  // Prompt & Streaming values
  const [searchQuery, setSearchQuery] = useState("");
  const [streamingTokenText, setStreamingTokenText] = useState("");
  const [lastTelemetry, setLastTelemetry] = useState<{ queries: string[]; fallback: boolean; sources: SourceChunk[] } | null>(null);
  
  // Side-by-Side Source Chunk Drawer state
  const [activeViewerSource, setActiveViewerSource] = useState<SourceChunk | null>(null);

  // Auto-scroll anchor point link
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // --- Check Auth Status on Mount ---
  useEffect(() => {
    const checkAuth = async () => {
      const u = await fetchCurrentUser();
      setCurrentUser(u);
    };
    checkAuth();
  }, []);

  // --- Load User Files when Auth Changes ---
  const reloadFiles = async () => {
    const files = await fetchUserFiles();
    setUploadedFiles(files);
  };

  useEffect(() => {
    reloadFiles();
    setSelectedFile(null);
    setActiveHistory([]);
  }, [currentUser]);

  // --- Pull Chat Log Threads When Selected File Target Changes ---
  useEffect(() => {
    const syncWorkspaceHistory = async () => {
      if (selectedFile) {
        setChatLoading(true);
        const historyLogs = await fetchChatHistory(selectedFile.file_name);
        setActiveHistory(historyLogs);
        setLastTelemetry(null);
        setChatLoading(false);
      } else {
        setActiveHistory([]);
        setLastTelemetry(null);
      }
    };
    syncWorkspaceHistory();
  }, [selectedFile]);

  // --- Auto-scroll Effect ---
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeHistory, streamingTokenText, chatLoading]);

  // --- Handlers ---
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetFile = e.target.files?.[0];
    if (!targetFile) return;

    setUploadLoading(true);
    setStatusMsg(null);
    try {
      const resp = await uploadPhysicalFile(targetFile);
      const freshFiles = await fetchUserFiles();
      setUploadedFiles(freshFiles);
      const matched = freshFiles.find(f => f.file_name === resp.filename);
      if (matched) setSelectedFile(matched);
      setStatusMsg({ type: "success", text: "File processed into isolated vector workspace!" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse file.";
      setStatusMsg({ type: "error", text: msg });
    } finally {
      setUploadLoading(false);
    }
  };

  const handleSearchExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !selectedFile) return;

    const userPromptText = searchQuery;
    setSearchQuery("");
    
    // Append user message locally
    setActiveHistory(prev => [...prev, { role: "user", content: userPromptText }]);
    setChatLoading(true);
    setStreamingTokenText("");
    setLastTelemetry(null);

    let accumulatedAnswer = "";

    await streamAgenticRag(
      userPromptText,
      selectedFile.file_name,
      (meta) => {
        setLastTelemetry(meta);
      },
      (deltaToken) => {
        accumulatedAnswer += deltaToken;
        setStreamingTokenText(accumulatedAnswer);
      },
      (fullAnswer) => {
        setActiveHistory(prev => [...prev, { role: "assistant", content: fullAnswer }]);
        setStreamingTokenText("");
        setChatLoading(false);
      },
      (err) => {
        alert(`Stream Error: ${err}`);
        setChatLoading(false);
      }
    );
  };

  const handleLogout = () => {
    clearAuthToken();
    setCurrentUser(null);
    setSelectedFile(null);
    setUploadedFiles([]);
    setActiveHistory([]);
  };

  const renderContentWithCitations = (text: string) => {
    const citationRegex = /\[(.*?\.(?:pdf|txt))\]/gi;
    const parts = text.split(citationRegex);
    
    if (parts.length === 1) return text;
    
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        const sourceMatch = lastTelemetry?.sources?.find(s => s.doc.toLowerCase() === part.toLowerCase()) || { doc: part, snippet: "Verified source chunk context." };
        return (
          <button
            key={index}
            onClick={() => setActiveViewerSource(sourceMatch)}
            className="inline-flex items-center space-x-1 mx-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono hover:bg-emerald-500/20 cursor-pointer transition-all"
            title="Click to view highlighted source chunk"
          >
            <BookOpen className="h-3 w-3 text-emerald-400" />
            <span>[{part}]</span>
          </button>
        );
      }
      return part;
    });
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      
      {/* AUTH MODAL */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(u) => {
          setCurrentUser(u);
          reloadFiles();
        }}
      />

      {/* SIDEBAR: FILE VAULT & USER PROFILE */}
      <aside className="w-80 border-r border-slate-900 bg-slate-950 p-6 flex flex-col justify-between hidden sm:flex">
        <div className="space-y-6 flex flex-col h-full overflow-hidden">
          
          {/* Top Brand Header */}
          <div className="flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-2.5">
              <div className="bg-emerald-500/10 p-2 rounded-xl border border-emerald-500/20">
                <Layers className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <h2 className="font-bold text-sm tracking-tight">ContextIQ Vault</h2>
                <p className="text-[10px] text-slate-500 font-mono">Status: Multi-Tenant Shield</p>
              </div>
            </div>
          </div>

          {/* User Account Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-2 overflow-hidden">
              <div className="bg-emerald-500/20 p-1.5 rounded-lg border border-emerald-500/30 text-emerald-400 flex-shrink-0">
                <User className="h-4 w-4" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-slate-200 truncate">{currentUser ? currentUser.name : "Guest User"}</p>
                <p className="text-[10px] text-slate-500 truncate">{currentUser ? currentUser.email : "Local Workspace Mode"}</p>
              </div>
            </div>
            {currentUser ? (
              <button onClick={handleLogout} title="Sign Out" className="text-slate-500 hover:text-red-400 p-1 cursor-pointer transition-colors">
                <LogOut className="h-4 w-4" />
              </button>
            ) : (
              <button onClick={() => setIsAuthOpen(true)} className="text-xs bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 px-2.5 py-1 rounded-lg flex items-center space-x-1 cursor-pointer transition-all">
                <LogIn className="h-3.5 w-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>

          <hr className="border-slate-900 flex-shrink-0" />

          {/* UPLOAD BOX */}
          <div className="flex-shrink-0">
            <label className="group flex flex-col items-center justify-center border border-dashed border-slate-800 hover:border-emerald-500/40 bg-slate-900/20 hover:bg-slate-900/50 rounded-xl p-5 text-center cursor-pointer transition-all">
              <UploadCloud className="h-6 w-6 text-slate-500 group-hover:text-emerald-400 mb-2 transition-colors" />
              <span className="text-xs font-medium text-slate-400 group-hover:text-slate-200">Upload PDF or TXT</span>
              <span className="text-[10px] text-slate-600 mt-0.5">Hybrid Vector & BM25 Indexing</span>
              <input type="file" accept=".pdf,.txt" onChange={handleFileChange} className="hidden" disabled={uploadLoading} />
            </label>
          </div>

          {/* FILE INVENTORY LIST */}
          <div className="space-y-3 flex-1 flex flex-col overflow-hidden">
            <div className="flex items-center space-x-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest flex-shrink-0">
              <FolderHeart className="h-3.5 w-3.5" />
              <span>Your Vault Inventory ({uploadedFiles.length})</span>
            </div>

            {uploadedFiles.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-4 italic flex-shrink-0">No documents in your isolated vault.</p>
            ) : (
              <div className="space-y-1.5 overflow-y-auto pr-1 flex-1 custom-scrollbar">
                {uploadedFiles.map((f) => (
                  <div
                    key={f.id}
                    onClick={() => setSelectedFile(selectedFile?.id === f.id ? null : f)}
                    className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition-all ${
                      selectedFile?.id === f.id 
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 shadow-md shadow-emerald-950/20" 
                        : "bg-slate-900/40 border-slate-900 text-slate-400 hover:border-slate-800 hover:bg-slate-900/80"
                    }`}
                  >
                    <div className="flex items-center space-x-2 overflow-hidden mr-2">
                      <FileText className={`h-4 w-4 flex-shrink-0 ${selectedFile?.id === f.id ? "text-emerald-400" : "text-slate-500"}`} />
                      <span className="text-xs font-medium truncate">{f.file_name}</span>
                    </div>
                    <span className="text-[9px] text-slate-600 font-mono flex-shrink-0">
                      {f.file_size ? `${(f.file_size / 1024).toFixed(1)} KB` : "Vault File"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Upload Notifications */}
        <div className="mt-4 space-y-2 flex-shrink-0">
          {uploadLoading && (
            <div className="bg-slate-900/50 border border-slate-800 text-xs text-slate-400 rounded-lg p-3 animate-pulse flex items-center space-x-2">
              <Cpu className="h-4 w-4 animate-spin text-emerald-400 flex-shrink-0" />
              <span>Indexing chunks & vectors...</span>
            </div>
          )}

          {statusMsg && !uploadLoading && (
            <div className={`p-3 rounded-lg border text-xs flex items-start space-x-2 ${
              statusMsg.type === "success" ? "bg-emerald-950/20 border-emerald-500/20 text-emerald-400" : "bg-red-950/20 border-red-500/20 text-red-400"
            }`}>
              {statusMsg.type === "success" ? <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" /> : <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />}
              <span>{statusMsg.text}</span>
            </div>
          )}
        </div>
      </aside>

      {/* CORE ACTIVE SEARCH ENGINE VIEWPORT MAIN */}
      <main className="flex-1 flex flex-col h-screen max-w-4xl mx-auto w-full justify-between p-6 lg:p-12 overflow-hidden relative">
        
        {!selectedFile ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center space-y-4 animate-fadeIn">
            <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full text-emerald-400 text-xs font-mono mb-2">
              <Zap className="h-3.5 w-3.5" />
              <span>Agentic RAG Engine Active</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
              Where knowledge begins.
            </h1>
            <p className="text-slate-400 text-sm max-w-md leading-relaxed">
              Select an uploaded file from your sidebar vault panel to activate focused conversation, streaming responses, and hybrid search.
            </p>
          </div>
        ) : (
          /* PERSISTENT CONVERSATION VIEWPORT BOARD */
          <div className="flex-1 w-full overflow-y-auto space-y-6 pr-2 mb-4 custom-scrollbar">
            
            {/* Thread Header Banner */}
            <div className="bg-slate-900/40 border border-slate-900/60 rounded-xl p-4 flex items-center justify-between sticky top-0 backdrop-blur-md z-20">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-300">Active Workspace Document:</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-emerald-300">
                  {selectedFile.file_name}
                </span>
              </div>
              <button 
                onClick={() => setSelectedFile(null)}
                className="text-[10px] text-slate-500 hover:text-slate-300 underline cursor-pointer transition-colors"
              >
                Close Scope
              </button>
            </div>

            {activeHistory.length === 0 && !chatLoading && !streamingTokenText && (
              <div className="text-center py-16 text-slate-600 text-xs italic">
                Conversation slate is empty. Ask any prompt or summary question about "{selectedFile.file_name}".
              </div>
            )}

            {/* Conversation Log Blocks */}
            {activeHistory.map((msg, index) => (
              <div 
                key={index} 
                className={`flex items-start space-x-4 p-5 rounded-2xl border transition-all animate-fadeIn ${
                  msg.role === "user" 
                    ? "bg-slate-900/40 border-slate-900/60 ml-12" 
                    : "bg-slate-900/10 border-slate-900/30 mr-12 shadow-md shadow-slate-950/40"
                }`}
              >
                <div className={`p-2 rounded-xl flex-shrink-0 ${
                  msg.role === "user" ? "bg-slate-800 text-slate-300" : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                }`}>
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                
                <div className="flex-1 space-y-2">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    {msg.role === "user" ? "You" : "ContextIQ Reasoning Matrix"}
                  </div>
                  <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.role === "assistant" ? renderContentWithCitations(msg.content) : msg.content}
                  </div>
                </div>
              </div>
            ))}

            {/* REAL-TIME TYPEWRITER STREAMING BLOCK */}
            {streamingTokenText && (
              <div className="flex items-start space-x-4 p-5 rounded-2xl border bg-slate-900/10 border-emerald-500/30 mr-12 shadow-lg shadow-emerald-950/20 animate-fadeIn">
                <div className="p-2 rounded-xl flex-shrink-0 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Bot className="h-4 w-4 animate-pulse" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-1">
                    <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span>
                    <span>Streaming Real-Time Agentic Answer...</span>
                  </div>
                  <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {renderContentWithCitations(streamingTokenText)}
                    <span className="inline-block w-2 h-4 bg-emerald-400 ml-1 animate-pulse"></span>
                  </div>
                </div>
              </div>
            )}

            {/* Active loading indicator */}
            {chatLoading && !streamingTokenText && (
              <div className="flex items-center space-x-3 bg-slate-900/30 border border-slate-900 p-4 rounded-xl text-xs text-slate-400 mr-12 animate-pulse">
                <Cpu className="h-4 w-4 text-emerald-400 animate-spin" />
                <span>Hybrid BM25 + Qdrant search & Cohere Reranking active...</span>
              </div>
            )}

            {/* Telemetry Metric Pills */}
            {lastTelemetry && (
              <div className="flex flex-wrap gap-1.5 items-center pt-2 px-2 animate-fadeIn">
                <span className="text-[10px] text-slate-500 flex items-center mr-1 uppercase tracking-wider font-bold">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-400 mr-1" /> Cognitive Expansion:
                </span>
                {lastTelemetry.queries?.map((term, i) => (
                  <span key={i} className="px-2.5 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-300 font-mono">
                    {"\""}{term}{"\""}
                  </span>
                ))}
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>
        )}

        {/* INPUT PROMPT COMMAND BAR */}
        <form onSubmit={handleSearchExecute} className="w-full max-w-3xl mx-auto relative mt-auto flex-shrink-0">
          <div className="flex items-center bg-slate-900/80 border border-slate-800 rounded-2xl p-2 focus-within:border-emerald-500/40 shadow-2xl transition-all">
            <div className="pl-3 text-slate-500">
              <Search className="h-5 w-5" />
            </div>
            <input
              type="text"
              placeholder={
                selectedFile 
                  ? `Ask anything about "${selectedFile.file_name}" (e.g. "what is this about?")...` 
                  : "Select an uploaded file on the sidebar to chat..."
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent px-3 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none"
              disabled={chatLoading || !selectedFile}
            />
            <button
              type="submit"
              disabled={chatLoading || !searchQuery.trim() || !selectedFile}
              className="bg-slate-100 hover:bg-slate-200 disabled:bg-slate-900 text-slate-950 disabled:text-slate-600 p-2.5 rounded-xl transition-all cursor-pointer flex-shrink-0"
            >
              <Search className="h-4 w-4" />
            </button>
          </div>
          <div className="text-center mt-2.5">
            <p className="text-[9px] text-slate-600 font-mono">
              🛡️ Permanent disk database & cryptographically salted Qdrant vector isolation.
            </p>
          </div>
        </form>

      </main>

      {/* SIDE-BY-SIDE INTERACTIVE SOURCE CHUNK DRAWER */}
      {activeViewerSource && (
        <aside className="w-96 border-l border-slate-900 bg-slate-950 p-6 flex flex-col justify-between animate-fadeIn z-30">
          <div className="space-y-4 flex flex-col h-full overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="h-4 w-4 text-emerald-400" />
                <h3 className="font-bold text-sm text-slate-200">Source Chunk Highlight</h3>
              </div>
              <button 
                onClick={() => setActiveViewerSource(null)}
                className="text-slate-500 hover:text-slate-200 p-1 cursor-pointer transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
              <p className="text-[10px] font-mono text-slate-500 uppercase">Document Source:</p>
              <p className="text-xs font-mono font-semibold text-emerald-400 mt-0.5">{activeViewerSource.doc}</p>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
              <p className="text-[10px] font-mono text-slate-500 uppercase">Extracted Factual Chunk:</p>
              <div className="p-4 rounded-xl bg-slate-900/40 border border-emerald-500/30 text-slate-200 text-xs leading-relaxed font-sans relative">
                <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-emerald-500/20 text-[9px] font-mono text-emerald-300 border border-emerald-500/30">
                  Grounded Snippet
                </div>
                "{activeViewerSource.snippet}"
              </div>
            </div>

            <div className="pt-3 border-t border-slate-900 text-center">
              <p className="text-[10px] text-slate-500 font-mono">
                Verified with Cohere Cross-Encoder Reranker
              </p>
            </div>
          </div>
        </aside>
      )}

    </div>
  );
}