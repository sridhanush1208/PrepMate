export type AgentName = "coach" | "interviewer" | "tutor" | "planner";

export interface Student {
  id: string;
  name: string;
  target_role: string;
  created_at?: number;
}

export interface Role {
  id: string;
  name: string;
}

export interface MemoryUsed {
  query: string;
  cypher: string;
  rows: number;
}

export type ChatEvent =
  | { type: "message"; agent: AgentName; text: string; memories_used: MemoryUsed[]; provider?: string }
  | { type: "handoff"; from: AgentName; to: AgentName; reason: string; topic: string }
  | { type: "memory"; agent: AgentName; kind: string; text: string }
  | { type: "user"; text: string };

export interface FactOrRule {
  id: string;
  kind: "Fact" | "Rule";
  text: string;
  ts: number;
  source_text: string | null;
  written_by: string | null;
  applies_to: string | null;
  about: string | null;
}

export interface GraphNode {
  id: number;
  label: string;
  name: string;
  props: Record<string, unknown>;
}

export interface GraphLink {
  source: number;
  target: number;
  type: string;
  props: Record<string, unknown>;
}

export interface Timeline {
  sessions: { session_id: string; started_at: number; summary: string | null; attempts: { topic: string; score: number; ts: number }[]; handoffs: number }[];
  mastery: { topic_id: string; topic: string; area: string; mastery: number; attempts: number; last_practiced: number }[];
}

export interface Plan {
  tasks: { id: string; title: string; due: number; agent: string; topic: string }[];
  due_for_revision: { topic: string; mastery: number; effective: number }[];
  ready_to_learn: { topic: string; role_weight: number; foundational: number }[];
  weak: { topic: string; mastery: number }[];
}

async function call<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${url} failed: ${res.status}`);
  return res.json();
}

export const api = {
  health: () => call<{ ok: boolean; llm: string | string[] }>("GET", "/api/health"),
  roles: () => call<Role[]>("GET", "/api/roles"),
  students: () => call<Student[]>("GET", "/api/students"),
  createStudent: (name: string, target_role: string) => call<Student>("POST", "/api/students", { name, target_role }),
  forget: (id: string) => call("DELETE", `/api/students/${id}`),
  startSession: (id: string) => call<{ session_id: string; events: ChatEvent[] }>("POST", `/api/students/${id}/sessions`),
  endSession: (id: string, sid: string) => call("POST", `/api/students/${id}/sessions/${sid}/end`),
  chat: (id: string, session_id: string, text: string, mode: string) =>
    call<{ events: ChatEvent[] }>("POST", `/api/students/${id}/chat`, { session_id, text, mode }),
  graph: (id: string) => call<{ nodes: GraphNode[]; links: GraphLink[] }>("GET", `/api/students/${id}/memory/graph`),
  facts: (id: string) => call<FactOrRule[]>("GET", `/api/students/${id}/memory/facts`),
  deleteMemory: (id: string, mid: string) => call("DELETE", `/api/students/${id}/memory/${mid}`),
  timeline: (id: string) => call<Timeline>("GET", `/api/students/${id}/memory/timeline`),
  plan: (id: string) => call<Plan>("GET", `/api/students/${id}/memory/plan`),
};

export const AGENTS: Record<AgentName, { label: string; emoji: string; color: string; bubble: string }> = {
  coach: { label: "Coach", emoji: "🟢", color: "#16a34a", bubble: "border-green-300 bg-green-50" },
  interviewer: { label: "Interviewer", emoji: "🔵", color: "#2563eb", bubble: "border-blue-300 bg-blue-50" },
  tutor: { label: "Tutor", emoji: "🟣", color: "#9333ea", bubble: "border-purple-300 bg-purple-50" },
  planner: { label: "Planner", emoji: "🟠", color: "#ea580c", bubble: "border-orange-300 bg-orange-50" },
};

export function ago(ms?: number | null): string {
  if (!ms) return "never";
  const days = (Date.now() - ms) / 86_400_000;
  if (days < 1 / 24) return "just now";
  if (days < 1) return `${Math.floor(days * 24)}h ago`;
  return `${Math.floor(days)}d ago`;
}
