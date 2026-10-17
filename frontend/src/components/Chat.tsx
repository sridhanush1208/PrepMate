import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import { AGENTS, ChatEvent, MemoryUsed } from "../api";

interface Props {
  events: ChatEvent[];
  busy: boolean;
  onSend: (text: string, mode: string) => void;
}

function MemoriesUsed({ used }: { used: MemoryUsed[] }) {
  const [open, setOpen] = useState(false);
  if (!used.length) return null;
  return (
    <div className="mt-1 text-xs text-gray-500">
      <button className="hover:text-gray-800" onClick={() => setOpen(!open)}>
        {open ? "▾" : "▸"} memories used ({used.length} graph queries)
      </button>
      {open && (
        <div className="mt-1 space-y-1">
          {used.map((u, i) => (
            <details key={i} className="rounded border border-gray-200 bg-white px-2 py-1">
              <summary className="cursor-pointer">
                <code>{u.query}</code> → {u.rows} row{u.rows === 1 ? "" : "s"}
              </summary>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-[11px] text-gray-700">{u.cypher}</pre>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Chat({ events, busy, onSend }: Props) {
  const [text, setText] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [events, busy]);

  const submit = () => {
    if (!text.trim() || busy) return;
    onSend(text.trim(), "chat");
    setText("");
  };

  return (
    <section className="flex min-h-0 flex-col rounded-xl border border-gray-200 bg-white">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {events.map((e, i) => {
          if (e.type === "user")
            return (
              <div key={i} className="flex justify-end">
                <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-gray-900 px-3 py-2 text-sm whitespace-pre-wrap text-white">{e.text}</div>
              </div>
            );
          if (e.type === "handoff")
            return (
              <div key={i} className="flex items-center gap-2 text-xs text-cyan-700">
                <div className="h-px flex-1 border-t border-dashed border-cyan-300" />
                <span className="rounded-full bg-cyan-50 px-3 py-1">
                  ↪ {AGENTS[e.from].label} → {AGENTS[e.to].label}: {e.reason}
                </span>
                <div className="h-px flex-1 border-t border-dashed border-cyan-300" />
              </div>
            );
          if (e.type === "memory")
            return (
              <div key={i} className="ml-2 text-xs text-gray-500">
                💾 <b>{AGENTS[e.agent]?.label ?? e.agent}</b> saved {e.kind}: {e.text}
              </div>
            );
          const a = AGENTS[e.agent];
          return (
            <div key={i} className="max-w-[92%]">
              <div className="mb-0.5 text-xs font-semibold" style={{ color: a.color }}>
                {a.emoji} {a.label}
              </div>
              <div className={`md rounded-2xl rounded-tl-sm border px-3 py-2 text-sm ${a.bubble}`}>
                <Markdown>{e.text}</Markdown>
              </div>
              <MemoriesUsed used={e.memories_used} />
            </div>
          );
        })}
        {busy && <div className="text-sm text-gray-400">thinking…</div>}
        <div ref={bottom} />
      </div>

      <div className="border-t border-gray-200 p-3">
        <div className="mb-2 flex flex-wrap gap-2">
          {[
            ["mock", "🎤 Mock interview"],
            ["teach", "📘 Teach me"],
            ["plan", "🗓 Plan my week"],
          ].map(([mode, label]) => (
            <button
              key={mode}
              disabled={busy}
              onClick={() => onSend(text.trim(), mode)}
              className="rounded-full border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {label}
            </button>
          ))}
          <span className="self-center text-xs text-gray-400">type a topic first to pick it, e.g. "BFS"</span>
        </div>
        <div className="flex gap-2">
          <textarea
            rows={2}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Answer the question, ask anything, or tell PrepMate how you like to learn…"
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
          />
          <button onClick={submit} disabled={busy} className="rounded-lg bg-gray-900 px-4 text-sm text-white disabled:opacity-50">
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
