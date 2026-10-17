import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { GraphLink, GraphNode } from "../api";

const COLORS: Record<string, string> = {
  Student: "#111827",
  Topic: "#0ea5e9",
  Session: "#64748b",
  Attempt: "#2563eb",
  Question: "#93c5fd",
  Fact: "#16a34a",
  Rule: "#9333ea",
  Agent: "#f59e0b",
  Handoff: "#06b6d4",
  Task: "#ea580c",
};

function masteryColor(m: number) {
  if (m >= 0.6) return "#16a34a";
  if (m >= 0.5) return "#ca8a04";
  return "#dc2626";
}

export default function MemoryGraph({ nodes, links }: { nodes: GraphNode[]; links: GraphLink[] }) {
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 400, h: 400 });
  const [selected, setSelected] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!box.current) return;
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }));
    ro.observe(box.current);
    return () => ro.disconnect();
  }, []);

  // topic colour = the student's mastery (from the KNOWS edge)
  const mastery = useMemo(() => {
    const m = new Map<number, number>();
    links.forEach((l) => {
      if (l.type === "KNOWS") m.set(l.target, Number(l.props.mastery ?? 0));
    });
    return m;
  }, [links]);

  const data = useMemo(
    () => ({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) }),
    [nodes, links],
  );

  return (
    <div className="relative h-full" ref={box}>
      <ForceGraph2D
        width={size.w}
        height={size.h}
        graphData={data}
        nodeId="id"
        cooldownTicks={120}
        linkColor={() => "#cbd5e1"}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkLabel={(l: any) => l.type}
        nodeLabel={(n: any) => `${n.label}: ${n.name}`}
        onNodeClick={(n: any) => setSelected(n as GraphNode)}
        nodeCanvasObject={(n: any, ctx, scale) => {
          const r = n.label === "Student" ? 7 : n.label === "Agent" ? 5.5 : 4.5;
          const color = n.label === "Topic" && mastery.has(n.id) ? masteryColor(mastery.get(n.id)!) : COLORS[n.label] ?? "#94a3b8";
          ctx.beginPath();
          ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
          if (scale > 1.2 || ["Student", "Topic", "Agent"].includes(n.label)) {
            ctx.font = `${10 / scale}px sans-serif`;
            ctx.fillStyle = "#334155";
            ctx.textAlign = "center";
            ctx.fillText(String(n.name).slice(0, 28), n.x, n.y + r + 9 / scale);
          }
        }}
      />
      <div className="pointer-events-none absolute top-2 left-2 flex flex-wrap gap-x-3 gap-y-1 rounded bg-white/80 px-2 py-1 text-[10px]">
        {Object.entries(COLORS).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: c }} />
            {k}
          </span>
        ))}
        <span className="text-gray-500">topic colour = mastery (red→green)</span>
      </div>
      {selected && (
        <div className="absolute right-2 bottom-2 max-w-[70%] rounded-lg border border-gray-200 bg-white p-2 text-xs shadow">
          <div className="mb-1 flex justify-between gap-3 font-semibold">
            <span>
              {selected.label}: {selected.name}
            </span>
            <button onClick={() => setSelected(null)}>✕</button>
          </div>
          <pre className="max-h-40 overflow-auto whitespace-pre-wrap text-gray-600">{JSON.stringify(selected.props, null, 1)}</pre>
        </div>
      )}
    </div>
  );
}
