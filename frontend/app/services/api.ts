function getApiBaseUrl(): string {
  let envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  envUrl = envUrl.trim();
  if (envUrl.endsWith("/")) envUrl = envUrl.slice(0, -1);
  if (!envUrl.includes("/api/v1")) envUrl += "/api/v1";
  return envUrl;
}

const API_BASE_URL = getApiBaseUrl();

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  created_at?: string;
}

export interface TrackedFile {
  id: string;
  file_name: string;
  file_size: number;
  created_at?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface SourceChunk {
  doc: string;
  snippet: string;
}

export interface ChatResponse {
  query: string;
  answer: string;
  meta: {
    expanded_search_terms: string[];
    fallback_triggered: boolean;
    sources?: SourceChunk[];
  };
}

export function getAuthToken(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("contextiq_token") || "dev_local_tenant_user_123";
  }
  return "dev_local_tenant_user_123";
}

export function setAuthToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("contextiq_token", token);
  }
}

export function clearAuthToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("contextiq_token");
    localStorage.removeItem("contextiq_user");
  }
}

async function handleResponse(resp: Response) {
  const contentType = resp.headers.get("content-type") || "";
  if (!resp.ok) {
    if (contentType.includes("application/json")) {
      const err = await resp.json();
      throw new Error(err.detail || "Request failed.");
    } else {
      throw new Error(`Backend server returned status ${resp.status}. If Render server was sleeping, please wait 30 seconds for warm up and try again.`);
    }
  }
  return await resp.json();
}

export async function registerUser(name: string, email: string, password: string): Promise<{ access_token: string; user: AuthUser }> {
  const resp = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password })
  });
  const data = await handleResponse(resp);
  setAuthToken(data.access_token);
  if (typeof window !== "undefined") {
    localStorage.setItem("contextiq_user", JSON.stringify(data.user));
  }
  return data;
}

export async function loginUser(email: string, password: string): Promise<{ access_token: string; user: AuthUser }> {
  const resp = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await handleResponse(resp);
  setAuthToken(data.access_token);
  if (typeof window !== "undefined") {
    localStorage.setItem("contextiq_user", JSON.stringify(data.user));
  }
  return data;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const token = getAuthToken();
  if (!token || token === "dev_local_tenant_user_123") return null;
  try {
    const resp = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    return null;
  }
}

export async function uploadPhysicalFile(file: File): Promise<{ status: string; filename: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${getAuthToken()}`
    },
    body: formData
  });

  return await handleResponse(response);
}

export async function fetchUserFiles(): Promise<TrackedFile[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/list`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${getAuthToken()}`,
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) return [];
    return await response.json();
  } catch (error: unknown) {
    console.error("❌ API Service Fetch Files Error:", error);
    return [];
  }
}

export async function fetchChatHistory(fileName: string): Promise<ChatMessage[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/history?file_name=${encodeURIComponent(fileName)}`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${getAuthToken()}`,
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) return [];
    return await response.json();
  } catch (error: unknown) {
    console.error("❌ API Service Fetch History Error:", error);
    return [];
  }
}

export async function queryAgenticRag(prompt: string, targetFileName?: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify({
      prompt: prompt,
      file_context_filter: targetFileName || null
    })
  });

  return await handleResponse(response);
}

export async function streamAgenticRag(
  prompt: string, 
  targetFileName: string | undefined, 
  onMeta: (meta: { queries: string[]; fallback: boolean; sources: SourceChunk[] }) => void,
  onToken: (token: string) => void,
  onDone: (fullAnswer: string) => void,
  onError: (err: string) => void
) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        prompt: prompt,
        file_context_filter: targetFileName || null
      })
    });

    if (!response.ok) {
      throw new Error(`Backend returned status ${response.status}. Please check backend connection.`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No readable stream received.");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.event === "meta") {
              onMeta({ queries: data.queries, fallback: data.fallback, sources: data.sources || [] });
            } else if (data.event === "token") {
              onToken(data.delta);
            } else if (data.event === "done") {
              onDone(data.full_answer);
            } else if (data.event === "error") {
              onError(data.message);
            }
          } catch (e) {
            console.error("SSE parse error:", e);
          }
        }
      }
    }
  } catch (err: any) {
    onError(err.message || "Streaming connection failed.");
  }
}