import { useCallback, useEffect, useState } from "react";
import { api, ChatEvent, Role, Student } from "./api";
import StudentBar from "./components/StudentBar";
import Chat from "./components/Chat";
import MemoryPanel from "./components/MemoryPanel";

export default function App() {
  const [students, setStudents] = useState<Student[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [current, setCurrent] = useState<Student | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<ChatEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [memoryVersion, setMemoryVersion] = useState(0);
  const [llm, setLlm] = useState<string>("");
  const [error, setError] = useState<string>("");

  const refreshStudents = useCallback(async () => {
    const list = await api.students();
    setStudents(list);
    return list;
  }, []);

  useEffect(() => {
    api.roles().then(setRoles).catch(() => setError("Backend not reachable. Is the API running?"));
    api.health().then((h) => setLlm(Array.isArray(h.llm) ? h.llm.join(" → ") : h.llm)).catch(() => {});
    refreshStudents().catch(() => {});
  }, [refreshStudents]);

  const open = useCallback(
    async (student: Student) => {
      if (current && sessionId) api.endSession(current.id, sessionId).catch(() => {});
      setCurrent(student);
      setEvents([]);
      setBusy(true);
      try {
        const res = await api.startSession(student.id);
        setSessionId(res.session_id);
        setEvents(res.events);
      } catch (e) {
        setError(String(e));
      } finally {
        setBusy(false);
        setMemoryVersion((v) => v + 1);
      }
    },
    [current, sessionId],
  );

  // end the session when the tab closes, so the next visit says "welcome back"
  useEffect(() => {
    const onUnload = () => {
      if (current && sessionId) navigator.sendBeacon(`/api/students/${current.id}/sessions/${sessionId}/end`);
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, [current, sessionId]);

  const send = async (text: string, mode: string) => {
    if (!current || !sessionId) return;
    const shown = text || { mock: "🎤 Mock interview", teach: "📘 Teach me", plan: "🗓 Plan my week" }[mode] || "";
    setEvents((ev) => [...ev, { type: "user", text: shown }]);
    setBusy(true);
    try {
      const res = await api.chat(current.id, sessionId, text, mode);
      setEvents((ev) => [...ev, ...res.events]);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
      setMemoryVersion((v) => v + 1);
    }
  };

  const create = async (name: string, role: string) => {
    const s = await api.createStudent(name, role);
    await refreshStudents();
    await open(s);
  };

  const forget = async () => {
    if (!current || !confirm(`Delete ALL of ${current.name}'s memory? This removes their graph.`)) return;
    await api.forget(current.id);
    setCurrent(null);
    setSessionId(null);
    setEvents([]);
    await refreshStudents();
  };

  return (
    <div className="flex h-full flex-col">
      <StudentBar
        students={students}
        roles={roles}
        current={current}
        llm={llm}
        onPick={open}
        onCreate={create}
        onForget={forget}
      />
      {error && (
        <div className="bg-red-50 px-4 py-2 text-sm text-red-700" onClick={() => setError("")}>
          {error} (click to dismiss)
        </div>
      )}
      {current && sessionId ? (
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-y-auto p-3 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:overflow-hidden">
          <Chat events={events} busy={busy} onSend={send} />
          <MemoryPanel student={current} version={memoryVersion} />
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center p-6 text-center text-gray-500">
          <div className="max-w-md">
            <div className="mb-3 text-5xl">🎯</div>
            <h1 className="mb-2 text-2xl font-semibold text-gray-800">PrepMate</h1>
            <p>
              A team of 4 AI agents (Coach, Interviewer, Tutor, Planner) that helps you prepare for placements.
              They remember you across sessions and share one memory graph in FalkorDB.
            </p>
            <p className="mt-3 text-sm">Pick a student above, or create a new one.</p>
          </div>
        </div>
      )}
    </div>
  );
}
