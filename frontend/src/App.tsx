import { useState, useRef, useEffect, type FormEvent } from "react";
import { MarkdownHooks as ReactMarkdown } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "./types";

const FAQ = [
  "Who is Jalin?",
  "What I do?",
  "Explore My Work",
  "Skills Overview",
  "Want to Work?",
];

// Hardcoded credentials — frontend-only auth gate for this personal demo
const CREDENTIALS = { username: "jalin", password: "raglab2024" };

const STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Mulish:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:      #e8d5b5;
    --surface: #f5ece0;
    --border:  #1a1a1a;
    --text:    #1a1a1a;
    --muted:   #6b5f50;
    --yellow:  #f0e040;
    --black:   #111111;
    --white:   #faf5ee;
  }

  body {
    font-family: 'Mulish', sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    overflow: hidden;
  }

  #root {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 1100px;
    margin: 0 auto;
    background: var(--bg);
  }

  /* ── Rainbow stripe ── */
  @keyframes bar-fly-in {
    0%   { transform: translateY(100%); opacity: 0; }
    100% { transform: translateY(0);    opacity: 1; }
  }

  .rainbow {
    height: 20px;
    flex-shrink: 0;
    display: flex;
    overflow: hidden;
  }

  .rainbow-bar {
    flex: 1;
    height: 100%;
    transform: translateY(100%);
    opacity: 0;
    animation: bar-fly-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  }

  /* ── Header ── */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px;
    flex-shrink: 0;
    border-bottom: 1.5px solid var(--border);
    background: var(--bg);
  }
  .header-brand {
    font-family: 'Mulish', sans-serif;
    font-weight: 700;
    font-size: 16px;
    letter-spacing: -0.2px;
    color: var(--text);
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 24px;
  }
  .header-tag {
    font-family: 'Mulish', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    background: var(--yellow);
    padding: 3px 10px;
    border-radius: 2px;
  }
  .status-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    color: var(--muted);
  }
  .status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4a8c5c;
  }

  /* ── Main layout ── */
  .main-layout {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .sidebar {
    width: 220px;
    flex-shrink: 0;
    border-right: 1.5px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 28px 28px 28px 20px;
    gap: 16px;
    background: var(--bg);
    overflow: visible;
  }
  .sidebar-label {
    font-family: 'Mulish', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 4px;
  }
  .new-chat-btn {
    position: relative;
    width: 100%;
    background: var(--white);
    color: var(--text);
    border: 2px solid var(--border);
    border-radius: 0;
    font-family: 'Mulish', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    line-height: 1.4;
    padding: 13px 14px;
    text-align: center;
    cursor: pointer;
    box-shadow: 4px 4px 0 0 var(--bg), 4px 4px 0 2px var(--border);
    transition: background 0.15s ease, transform 0.22s ease-out, box-shadow 0.22s ease-out;
  }
  .new-chat-btn:hover {
    background: var(--surface);
  }
  .new-chat-btn:active {
    transform: translate(4px, 4px);
    box-shadow: 0px 0px 0 0 var(--bg), 0px 0px 0 2px var(--border);
    transition: background 0.05s, transform 0.06s ease-in, box-shadow 0.06s ease-in;
  }
  .sidebar-divider {
    height: 1.5px;
    background: var(--border);
    margin: 0;
    flex-shrink: 0;
  }
  .faq-btn {
    position: relative;
    z-index: 0;
    width: 100%;
    background: var(--black);
    color: var(--white);
    border: 2px solid var(--border);
    border-radius: 0;
    font-family: 'Mulish', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
    line-height: 1.4;
    padding: 13px 14px;
    text-align: center;
    cursor: pointer;
    transition: background 0.15s ease, transform 0.22s ease-out;
  }
  .faq-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    border: 2px solid var(--border);
    background: transparent;
    transform: translate(7px, 7px);
    z-index: -1;
    transition: transform 0.22s ease-out;
  }
  .faq-btn:hover:not(:disabled) {
    background: #2a2a2a;
  }
  .faq-btn:active:not(:disabled) {
    transform: translate(7px, 7px);
    transition: background 0.05s, transform 0.06s ease-in;
  }
  .faq-btn:active:not(:disabled)::after {
    transform: translate(0, 0);
    transition: transform 0.06s ease-in;
  }
  .faq-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* ── Chat column ── */
  .chat-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* ── Hero label ── */
  .hero {
    padding: 28px 32px 0;
    flex-shrink: 0;
  }
  .hero h1 {
    font-family: 'Abril Fatface', serif;
    font-size: 32px;
    line-height: 1.15;
    color: var(--text);
    letter-spacing: -0.5px;
  }
  .hero h1 mark {
    background: var(--yellow);
    color: var(--text);
    padding: 0 4px;
  }
  .hero p {
    font-size: 13px;
    color: var(--muted);
    margin-top: 8px;
    font-weight: 400;
    line-height: 1.6;
  }
  .divider {
    height: 1.5px;
    background: var(--border);
    margin: 20px 32px 0;
    flex-shrink: 0;
  }

  /* ── Messages ── */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    scrollbar-width: thin;
    scrollbar-color: #c9b89a transparent;
  }
  .messages::-webkit-scrollbar { width: 4px; }
  .messages::-webkit-scrollbar-thumb { background: #c9b89a; border-radius: 4px; }

  /* Empty state */
  .empty {
    margin: auto;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  .empty-title {
    font-family: 'Abril Fatface', serif;
    font-size: 22px;
    color: var(--text);
  }
  .empty p {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.7;
    max-width: 300px;
  }
  .empty code {
    font-family: monospace;
    background: var(--surface);
    border: 1px solid #c9b89a;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
  }

  /* Message rows */
  .msg-row {
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }
  .msg-row.user { flex-direction: row-reverse; }

  /* Label chip */
  .label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 2px;
    flex-shrink: 0;
    margin-top: 4px;
    white-space: nowrap;
  }
  .label.user {
    background: var(--black);
    color: var(--white);
  }
  .label.assistant {
    background: var(--surface);
    border: 2px solid var(--border);
    color: var(--text);
  }

  /* Bubble */
  .bubble {
    max-width: 74%;
    padding: 14px 18px;
    font-size: 13px;
    line-height: 1.8;
    word-break: break-word;
    white-space: pre-wrap;
  }
  .bubble.user {
    background: var(--black);
    color: var(--white);
    box-shadow: 4px 4px 0 0 #4a4a4a;
    border-radius: 2px;
  }
  .bubble.assistant {
    background: var(--surface);
    border: 2px solid var(--border);
    box-shadow: 4px 4px 0 0 var(--border);
    border-radius: 2px;
    color: var(--text);
    font-family: 'Mulish', sans-serif;
    letter-spacing: 0.02em;
    white-space: normal;
  }

  /* Markdown */
  .bubble.assistant h1,
  .bubble.assistant h2,
  .bubble.assistant h3 {
    font-family: 'Mulish', sans-serif;
    font-weight: 700;
    color: var(--text);
    margin: 14px 0 6px;
    line-height: 1.3;
  }
  .bubble.assistant h1 { font-size: 15px; }
  .bubble.assistant h2 { font-size: 14px; }
  .bubble.assistant h3 { font-size: 13px; }
  .bubble.assistant p { margin: 6px 0; }
  .bubble.assistant p:first-child { margin-top: 0; }
  .bubble.assistant p:last-child { margin-bottom: 0; }
  .bubble.assistant strong { font-weight: 700; }
  .bubble.assistant em { font-style: italic; color: var(--muted); }
  .bubble.assistant ul, .bubble.assistant ol { padding-left: 20px; margin: 10px 0; }
  .bubble.assistant li { margin: 10px 0; }
  .bubble.assistant a { color: var(--text); font-weight: 700; }
  .bubble.assistant code {
    font-family: monospace;
    background: var(--bg);
    border: 1px solid #c9b89a;
    padding: 1px 5px;
    border-radius: 2px;
    font-size: 12.5px;
  }
  .bubble.assistant pre {
    background: var(--bg);
    border: 2px solid var(--border);
    padding: 12px;
    border-radius: 2px;
    overflow-x: auto;
    margin: 8px 0;
  }
  .bubble.assistant pre code { background: none; border: none; padding: 0; }
  .bubble.assistant hr { border: none; border-top: 1.5px solid var(--border); margin: 10px 0; }

  /* Tables */
  .bubble.assistant table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 12.5px;
  }
  .bubble.assistant th {
    background: var(--black);
    color: var(--white);
    font-weight: 700;
    padding: 8px 14px;
    text-align: left;
    border: 1.5px solid var(--border);
    letter-spacing: 0.04em;
    font-family: 'Mulish', sans-serif;
  }
  .bubble.assistant td {
    padding: 8px 14px;
    border: 1.5px solid var(--border);
    background: var(--white);
    vertical-align: top;
    line-height: 1.6;
  }
  .bubble.assistant tr:nth-child(even) td {
    background: var(--bg);
  }

  /* Cursor */
  .cursor::after {
    content: '▍';
    animation: blink 1s step-start infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }

  /* ── Toolbar ── */
  .toolbar-wrap {
    flex-shrink: 0;
    border-top: 1.5px solid var(--border);
    background: var(--bg);
  }
  .toolbar {
    display: flex;
    gap: 10px;
    align-items: stretch;
    padding: 16px 32px;
  }
  .input-wrap {
    flex: 1;
    background: var(--surface);
    border: 2px solid var(--border);
    box-shadow: 3px 3px 0 0 var(--border);
    display: flex;
    align-items: center;
    padding: 0 14px;
    border-radius: 2px;
  }
  .toolbar input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    padding: 13px 0;
    font-size: 14px;
    color: var(--text);
    font-family: 'Mulish', sans-serif;
    font-weight: 500;
  }
  .toolbar input::placeholder { color: #a09070; }

  .btn {
    border: 2px solid var(--border);
    border-radius: 2px;
    font-family: 'Mulish', sans-serif;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.22s ease-out, box-shadow 0.22s ease-out;
    letter-spacing: 0.2px;
    padding: 0 20px;
  }
  .btn:active { transform: translate(2px, 2px); box-shadow: none !important; transition: transform 0.06s ease-in, box-shadow 0.06s ease-in; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  .btn-ingest {
    background: var(--surface);
    color: var(--text);
    box-shadow: 3px 3px 0 0 var(--border);
  }
  .btn-ingest:hover:not(:disabled) { background: var(--yellow); }

  .btn-send {
    background: var(--black);
    color: var(--white);
    box-shadow: 3px 3px 0 0 var(--border);
    padding: 0 22px;
    font-size: 18px;
  }
  .btn-send:hover:not(:disabled) { background: #333; }

  /* Notice */
  .notice {
    text-align: center;
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    padding: 6px 32px;
    border-top: 1px solid #c9b89a;
    background: var(--surface);
    font-family: 'Mulish', sans-serif;
  }
  .notice.success { color: #4a8c5c; }
  .notice.error { color: #a03030; }

  /* ── Login screen ── */
  .login-screen {
    position: fixed;
    inset: 0;
    background: var(--bg);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .login-card {
    width: 360px;
    background: var(--surface);
    border: 2px solid var(--border);
    box-shadow: 6px 6px 0 0 var(--border);
    padding: 40px 36px;
    display: flex;
    flex-direction: column;
    gap: 22px;
  }

  .login-title {
    font-family: 'Abril Fatface', serif;
    font-size: 26px;
    color: var(--text);
    letter-spacing: -0.4px;
    line-height: 1.2;
  }

  .login-title mark {
    background: var(--yellow);
    color: var(--text);
    padding: 0 4px;
  }

  .login-subtitle {
    font-size: 12px;
    color: var(--muted);
    margin-top: -14px;
    font-weight: 400;
    line-height: 1.6;
  }

  .login-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .login-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .login-input {
    background: var(--bg);
    border: 2px solid var(--border);
    border-radius: 2px;
    padding: 11px 14px;
    font-size: 14px;
    font-family: 'Mulish', sans-serif;
    font-weight: 500;
    color: var(--text);
    outline: none;
    width: 100%;
    transition: box-shadow 0.15s;
  }

  .login-input:focus {
    box-shadow: 3px 3px 0 0 var(--border);
  }

  .login-input::placeholder { color: #a09070; }

  .login-btn {
    background: var(--black);
    color: var(--white);
    border: 2px solid var(--border);
    border-radius: 2px;
    padding: 13px;
    font-family: 'Mulish', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    box-shadow: 4px 4px 0 0 var(--border);
    transition: background 0.15s, transform 0.22s ease-out, box-shadow 0.22s ease-out;
    width: 100%;
  }

  .login-btn:hover { background: #2a2a2a; }

  .login-btn:active {
    transform: translate(4px, 4px);
    box-shadow: 0 0 0 0 var(--border);
    transition: transform 0.06s ease-in, box-shadow 0.06s ease-in;
  }

  .login-error {
    font-size: 12px;
    font-weight: 600;
    color: #a03030;
    text-align: center;
    margin-top: -10px;
  }

  /* Logout button in header */
  .btn-logout {
    font-family: 'Mulish', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: transparent;
    color: var(--muted);
    border: 1.5px solid var(--muted);
    border-radius: 2px;
    padding: 4px 10px;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .btn-logout:hover {
    color: var(--text);
    border-color: var(--border);
  }
`;

function uid() {
  return Math.random().toString(36).slice(2);
}

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (username === CREDENTIALS.username && password === CREDENTIALS.password) {
      localStorage.setItem("rl_auth", "1");
      onLogin();
    } else {
      setError("Invalid username or password.");
      setPassword("");
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div>
          <div className="login-title"><mark>Sign in</mark> to continue</div>
          <div className="login-subtitle">Access Jalin's RAG Lab assistant</div>
        </div>
        <div className="login-field">
          <label className="login-label" htmlFor="login-username">Username</label>
          <input
            id="login-username"
            className="login-input"
            type="text"
            autoComplete="username"
            placeholder="Enter username"
            value={username}
            onChange={(e) => { setUsername(e.target.value); setError(""); }}
          />
        </div>
        <div className="login-field">
          <label className="login-label" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            className="login-input"
            type="password"
            autoComplete="current-password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setError(""); }}
          />
        </div>
        {error && <div className="login-error">{error}</div>}
        <button className="login-btn" type="submit">Sign in</button>
      </form>
    </div>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(() => localStorage.getItem("rl_auth") === "1");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [notice, setNotice] = useState<{ text: string; type: "success" | "error" | "info" } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const streamingIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  function logout() {
    localStorage.removeItem("rl_auth");
    setAuthed(false);
    newChat();
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function newChat() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    streamingIdRef.current = null;
    setMessages([]);
    setStreaming(false);
    setInput("");
    setNotice(null);
  }

  function showNotice(text: string, type: "success" | "error" | "info" = "info") {
    setNotice({ text, type });
    setTimeout(() => setNotice(null), 5000);
  }

  async function sendQuery(query: string) {
    if (!query.trim() || streaming) return;

    const userMsg: Message = { id: uid(), role: "user", content: query };
    const assistantId = uid();
    streamingIdRef.current = assistantId;
    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: "assistant", content: "" }]);
    setStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).replace(/\\n/g, "\n");
          if (data === "[DONE]") break;
          setMessages((prev) =>
            prev.map((m) => m.id === assistantId ? { ...m, content: m.content + data } : m)
          );
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: "Error: could not reach the backend." } : m
        )
      );
    } finally {
      abortControllerRef.current = null;
      setStreaming(false);
      streamingIdRef.current = null;
    }
  }

  async function sendMessage() {
    const query = input.trim();
    if (!query) return;
    setInput("");
    await sendQuery(query);
  }

  async function triggerIngest() {
    showNotice("Ingesting documents...", "info");
    try {
      const res = await fetch("/api/ingest", { method: "POST" });
      const data = await res.json();
      if (data.status === "no_documents") {
        showNotice("No documents found in backend/data/", "error");
      } else {
        showNotice(`Done — ${data.chunks} chunks from ${data.sources?.length ?? 0} file(s)`, "success");
      }
    } catch {
      showNotice("Ingest failed — is the backend running?", "error");
    }
  }

  if (!authed) {
    return (
      <>
        <style>{STYLES}</style>
        <LoginScreen onLogin={() => setAuthed(true)} />
      </>
    );
  }

  return (
    <>
      <style>{STYLES}</style>

      <div className="rainbow">
        {[
          '#c9a97a','#4a8c5c','#c96b5a','#9090c8','#e8d040','#909090','#7a3050',
          '#d47a6a','#2a4a7a','#8a2030','#e8a0b0','#9050a0','#a04020','#f0ead8',
        ].map((color, i) => (
          <div
            key={color}
            className="rainbow-bar"
            style={{ background: color, animationDelay: `${i * 0.06}s` }}
          />
        ))}
      </div>

      <header>
        <span className="header-brand">Jalin Bright</span>
        <div className="header-right">
          <span className="header-tag">RAG Lab</span>
          <div className="status-wrap">
            <div className="status-dot" />
            online
          </div>
          <button className="btn-logout" onClick={logout}>Sign out</button>
        </div>
      </header>

      <div className="main-layout">

        {/* ── Sidebar ── */}
        <aside className="sidebar">
          <button className="new-chat-btn" onClick={newChat}>
            + New Chat
          </button>
          <div className="sidebar-divider" />
          <span className="sidebar-label">Quick questions</span>
          {FAQ.map((q) => (
            <button
              key={q}
              className="faq-btn"
              onClick={() => sendQuery(q)}
              disabled={streaming}
            >
              {q}
            </button>
          ))}
        </aside>

        {/* ── Chat column ── */}
        <div className="chat-col">
          <div className="hero">
            <h1><mark>Ask</mark> me anything</h1>
            <p>Your personal AI, powered by Jalin's knowledge base.</p>
          </div>
          <div className="divider" />

          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">
                <p className="empty-title">Start a conversation</p>
                <p>
                  Drop files into <code>backend/data/</code>, click Ingest, then ask anything.
                </p>
              </div>
            )}

            {messages.map((m) => (
              <div key={m.id} className={`msg-row ${m.role}`}>
                <span className={`label ${m.role}`}>
                  {m.role === "user" ? "You" : "AI"}
                </span>
                <div className={`bubble ${m.role}`}>
                  {m.role === "assistant" ? (
                    m.content ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ href, children }) => (
                            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
                          ),
                        }}
                      >{m.content}</ReactMarkdown>
                    ) : (
                      <span className="cursor" />
                    )
                  ) : (
                    <span style={{ whiteSpace: 'pre-wrap' }}>{m.content}</span>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {notice && <div className={`notice ${notice.type}`}>{notice.text}</div>}

          <div className="toolbar-wrap">
            <div className="toolbar">
              <button className="btn btn-ingest" onClick={triggerIngest} disabled={streaming}>
                Ingest
              </button>
              <div className="input-wrap">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask something about Jalin..."
                  disabled={streaming}
                />
              </div>
              <button className="btn btn-send" onClick={sendMessage} disabled={streaming || !input.trim()}>
                ↑
              </button>
            </div>
          </div>
        </div>

      </div>
    </>
  );
}
