import { useState } from "react";
import { Role, Student } from "../api";

interface Props {
  students: Student[];
  roles: Role[];
  current: Student | null;
  llm: string;
  onPick: (s: Student) => void;
  onCreate: (name: string, role: string) => void;
  onForget: () => void;
}

export default function StudentBar({ students, roles, current, llm, onPick, onCreate, onForget }: Props) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("product_sde");
  const roleName = (id: string) => roles.find((r) => r.id === id)?.name ?? id;

  return (
    <header className="flex flex-wrap items-center gap-3 border-b border-gray-200 bg-white px-4 py-2.5">
      <div className="mr-2 text-lg font-bold">🎯 PrepMate</div>
      <select
        className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        value={current?.id ?? ""}
        onChange={(e) => {
          const s = students.find((x) => x.id === e.target.value);
          if (s) onPick(s);
        }}
      >
        <option value="" disabled>
          Choose student…
        </option>
        {students.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      {current && <span className="text-sm text-gray-500">target: {roleName(current.target_role)}</span>}

      {adding ? (
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) onCreate(name.trim(), role);
            setAdding(false);
            setName("");
          }}
        >
          <input
            autoFocus
            className="w-32 rounded-md border border-gray-300 px-2 py-1 text-sm"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <select className="rounded-md border border-gray-300 px-2 py-1 text-sm" value={role} onChange={(e) => setRole(e.target.value)}>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <button className="rounded-md bg-gray-900 px-3 py-1 text-sm text-white">Create</button>
          <button type="button" className="text-sm text-gray-500" onClick={() => setAdding(false)}>
            cancel
          </button>
        </form>
      ) : (
        <button className="rounded-md border border-gray-300 px-2 py-1 text-sm hover:bg-gray-50" onClick={() => setAdding(true)}>
          + New student
        </button>
      )}

      <div className="ml-auto flex items-center gap-3">
        {llm && <span className="text-xs text-gray-400">LLM: {llm}</span>}
        {current && (
          <button className="rounded-md border border-red-200 px-2 py-1 text-sm text-red-600 hover:bg-red-50" onClick={onForget}>
            Forget me
          </button>
        )}
      </div>
    </header>
  );
}
