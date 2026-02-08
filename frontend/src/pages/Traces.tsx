import { useEffect, useState, useMemo } from "react";
import { api, type Trace } from "../api/client";

export default function Traces() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api
      .get("/traces")
      .then((res) => setTraces(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // 🔍 Filter ONLY by trace_name (case-insensitive)
  const filteredTraces = useMemo(() => {
    if (!search.trim()) return traces;

    const q = search.toLowerCase();
    return traces.filter((t) =>
      t.trace_name?.toLowerCase().includes(q)
    );
  }, [traces, search]);

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Loading traces…</div>;
  }

  return (
    <div className="space-y-4 text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Traces</h1>
          <p className="text-xs text-gray-400">
            {filteredTraces.length} traces
          </p>
        </div>

        {/* 🔍 Search */}
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by trace name…"
          className="bg-[#161a23] border border-gray-700 rounded-md px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500 w-56"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-[#1f242d] bg-[#0d1117]">
        <table className="min-w-full text-xs">
          <thead className="bg-[#161b22] border-b border-[#1f242d]">
            <tr className="text-gray-400">
              <th className="px-3 py-2 text-left font-medium">Timestamp</th>
              <th className="px-3 py-2 text-left font-medium">Name</th>
              <th className="px-3 py-2 text-left font-medium w-[40%]">Input</th>
              <th className="px-3 py-2 text-left font-medium">Latency</th>
              <th className="px-3 py-2 text-left font-medium">Tokens</th>
              <th className="px-3 py-2 text-left font-medium">Cost</th>
              <th className="px-3 py-2 text-left font-medium">Scores</th>
            </tr>
          </thead>

          <tbody>
            {filteredTraces.map((t) => (
              <tr
                key={t.trace_id}
                className="border-b border-[#1f242d] hover:bg-[#161a23] transition"
              >
                {/* Timestamp */}
                <td className="px-3 py-2 text-gray-400 whitespace-nowrap">
                  {new Date(t.timestamp).toLocaleString()}
                </td>

                {/* Trace Name */}
                <td className="px-3 py-2">
                  <span
                    className="px-2 py-0.5 rounded-full bg-[#0f172a] border border-[#1f2937] text-xs font-medium text-gray-200 whitespace-nowrap"
                    title={`Trace ID: ${t.trace_id}`}
                  >
                    {t.trace_name}
                  </span>
                </td>

                {/* Input */}
                <td
                  className="px-3 py-2 text-gray-300 truncate max-w-[520px] leading-tight"
                  title={t.input}
                >
                  {t.input}
                </td>

                {/* Latency */}
                <td className="px-3 py-2 text-gray-300 whitespace-nowrap">
                  {t.latency_ms}ms
                </td>

                {/* Tokens */}
                <td className="px-3 py-2 text-gray-300 whitespace-nowrap">
                  {t.tokens}
                </td>

                {/* Cost */}
                <td className="px-3 py-2 text-gray-300 whitespace-nowrap">
                  ${t.cost.toFixed(5)}
                </td>

                {/* Scores */}
                <td className="px-3 py-2">
                  <div className="flex gap-1.5 flex-wrap max-w-[260px]">
                    {Object.entries(t.scores || {}).map(([k, v]) => (
                      <span
                        key={k}
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap
                          ${
                            v < 0.3
                              ? "bg-[#3a1d16] text-[#ffb29b]"
                              : v < 0.6
                              ? "bg-[#2f1e0a] text-[#fcd34d]"
                              : "bg-[#0d2a1f] text-[#6ee7b7]"
                          }`}
                      >
                        {k}: {Number(v).toFixed(2)}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}

            {/* Empty state */}
            {filteredTraces.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-3 py-6 text-center text-gray-500 text-sm"
                >
                  No traces match “{search}”
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
