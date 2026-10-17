import { useEffect, useState } from "react";
import { ago, AGENTS, AgentName, api, FactOrRule, GraphLink, GraphNode, Plan, Student, Timeline } from "../api";
import MemoryGraph from "./MemoryGraph";

const TABS = ["Graph", "Facts & Rules", "Timeline", "Plan"] as const;
type Tab = (typeof TABS)[number];

function Bar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.6 ? "bg-green-500" : value >= 0.5 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="h-2 w-24 rounded bg-gray-200">
      <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

const agentLabel = (a: string | null) => (a && AGENTS[a as AgentName]?.label) || a || "?";

export default function MemoryPanel({ student, version }: { student: Student; version: number }) {
  const [tab, setTab] = useState<Tab>("Graph");
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
  const [facts, setFacts] = useState<FactOrRule[]>([]);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);

  const load = () => {
    const id = student.id;
    if (tab === "Graph") api.graph(id).then(setGraph);
    if (tab === "Facts & Rules") api.facts(id).then(setFacts);
    if (tab === "Timeline") api.timeline(id).then(setTimeline);
    if (tab === "Plan") api.plan(id).then(setPlan);
  };

  useEffect(load, [student.id, version, tab]);

  return (
    <section className="flex min-h-[420px] flex-col rounded-xl border border-gray-200 bg-white">
      <div className="flex items-center gap-1 border-b border-gray-200 px-3 pt-2">
        <span className="mr-2 text-sm font-semibold">🧠 What PrepMate remembers about {student.name}</span>
        <div className="ml-auto flex gap-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-t-md px-2.5 py-1 text-xs ${tab === t ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "Graph" && <MemoryGraph nodes={graph.nodes} links={graph.links} />}

        {tab === "Facts & Rules" && (
          <ul className="divide-y divide-gray-100 p-2 text-sm">
            {facts.length === 0 && <li className="p-3 text-gray-400">Nothing remembered yet.</li>}
            {facts.map((f) => (
              <li key={f.id} className="flex gap-2 p-2">
                <span
                  className={`h-fit rounded px-1.5 py-0.5 text-[10px] font-semibold ${f.kind === "Rule" ? "bg-purple-100 text-purple-700" : "bg-green-100 text-green-700"}`}
                >
                  {f.kind === "Rule" ? "RULE (procedural)" : "FACT (semantic)"}
                </span>
                <div className="flex-1">
                  <div>
                    {f.text}
                    {f.kind === "Rule" && <span className="text-gray-500"> → followed by {agentLabel(f.applies_to)}</span>}
                  </div>
                  <div className="text-xs text-gray-500">
                    saved by {agentLabel(f.written_by)} {ago(f.ts)}
                    {f.source_text && <> · from your message: “{f.source_text.slice(0, 90)}”</>}
                  </div>
                </div>
                <button
                  title="Forget this"
                  className="h-fit text-gray-400 hover:text-red-600"
                  onClick={() => api.deleteMemory(student.id, f.id).then(load)}
                >
                  🗑
                </button>
              </li>
            ))}
          </ul>
        )}

        {tab === "Timeline" && timeline && (
          <div className="space-y-4 p-3 text-sm">
            <div>
              <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Mastery (semantic memory)</h3>
              {timeline.mastery.length === 0 && <div className="text-gray-400">No topics practised yet.</div>}
              {timeline.mastery.map((m) => (
                <div key={m.topic_id} className="flex items-center gap-2 py-0.5">
                  <span className="w-48 truncate">{m.topic}</span>
                  <Bar value={m.mastery} />
                  <span className="text-xs text-gray-500">
                    {m.mastery.toFixed(2)} · {m.attempts} tries · {ago(m.last_practiced)}
                  </span>
                </div>
              ))}
            </div>
            <div>
              <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Sessions (episodic memory)</h3>
              {timeline.sessions.map((s) => (
                <div key={s.session_id} className="border-l-2 border-gray-300 py-1 pl-3">
                  <div className="text-xs text-gray-500">
                    {new Date(s.started_at).toLocaleString()} · {ago(s.started_at)}
                    {s.handoffs > 0 && ` · ${s.handoffs} handoff${s.handoffs > 1 ? "s" : ""}`}
                  </div>
                  <div>{s.summary ?? "(in progress)"}</div>
                  {s.attempts.length > 0 && (
                    <div className="text-xs text-gray-600">
                      {s.attempts.map((a) => `${a.topic} ${a.score.toFixed(1)}`).join(" · ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "Plan" && plan && (
          <div className="space-y-4 p-3 text-sm">
            <div>
              <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Shared task board</h3>
              {plan.tasks.length === 0 && <div className="text-gray-400">No open tasks. Try “Plan my week”.</div>}
              {plan.tasks.map((t) => (
                <div key={t.id} className="flex items-center gap-2 py-0.5">
                  <span>☐</span>
                  <span className="flex-1">{t.title}</span>
                  <span className="text-xs" style={{ color: AGENTS[t.agent as AgentName]?.color }}>
                    {agentLabel(t.agent)}
                  </span>
                  <span className="text-xs text-gray-500">due {new Date(t.due).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Weak</h3>
                {plan.weak.map((w) => (
                  <div key={w.topic}>
                    {w.topic} <span className="text-xs text-red-600">{w.mastery.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Fading (revise)</h3>
                {plan.due_for_revision.map((d) => (
                  <div key={d.topic}>
                    {d.topic} <span className="text-xs text-yellow-700">{d.mastery.toFixed(2)} → {d.effective.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="mb-1 text-xs font-semibold text-gray-500 uppercase">Ready to learn</h3>
                {plan.ready_to_learn.map((r) => (
                  <div key={r.topic}>{r.topic}</div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
