import React from "react";
import { type Evaluator } from "../api/client";

interface EvaluatorsTableProps {
  evaluators: Evaluator[];
}

const EvaluatorsTable: React.FC<EvaluatorsTableProps> = ({ evaluators }) => {
  const rows = evaluators || [];

  return (
    <div className="bg-[#161a23] border border-gray-800 rounded-2xl overflow-hidden">
      
      {/* Header */}
      <div className="p-6 border-b border-gray-800 bg-[#1c212e]/40">
        <h3 className="text-lg font-bold text-white">Active Evaluators</h3>
      </div>

      {rows.length === 0 ? (
        <div className="p-10 text-center text-gray-500 text-sm">
          No evaluators found
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[900px]">
            
            {/* Table Header */}
            <thead className="bg-[#161a23]">
              <tr className="border-b border-gray-800/80">
                {[
                  "Name",
                  "Status",
                  "Template",
                  "Score Name",
                  "Target",
                  "Sampling",
                  "Created",
                ].map((h) => (
                  <th
                    key={h}
                    className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>

            {/* Table Body */}
            <tbody>
              {rows.map((ev, i) => {
                const isActive = ev.status === "active";
                const samplingPct =
                  typeof ev.execution?.sampling_rate === "number"
                    ? `${ev.execution.sampling_rate * 100}%`
                    : "-";

                return (
                  <tr
                    key={ev.id || i}
                    className="border-b border-gray-800/40 hover:bg-[#1c212e]/40 transition-colors"
                  >
                    {/* Name */}
                    <td className="px-8 py-6 text-sm font-bold text-gray-200">
                      {ev.name || ev.score_name}
                    </td>

                    {/* Status Badge */}
                    <td className="px-8 py-6">
                      <span
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-black uppercase border ${
                          isActive
                            ? "bg-green-500/10 text-green-500 border-green-500/20"
                            : "bg-gray-700/20 text-gray-400 border-gray-600"
                        }`}
                      >
                        <div
                          className={`w-1.5 h-1.5 rounded-full ${
                            isActive ? "bg-green-500" : "bg-gray-500"
                          }`}
                        />
                        {ev.status}
                      </span>
                    </td>

                    {/* Template Badge */}
                    <td className="px-8 py-6">
                      <span className="px-3 py-1 bg-gray-800/60 text-gray-300 text-xs font-bold rounded-lg border border-gray-700/50">
                        {ev.template?.id}
                      </span>
                    </td>

                    {/* Score Name */}
                    <td className="px-8 py-6 text-sm text-gray-400 font-mono">
                      {ev.score_name}
                    </td>

                    {/* Target Pill */}
                    <td className="px-8 py-6">
                      <span className="px-2 py-0.5 bg-gray-900 border border-gray-800 text-gray-400 text-[9px] font-black rounded uppercase tracking-widest">
                        {ev.target}
                      </span>
                    </td>

                    {/* Sampling */}
                    <td className="px-8 py-6 text-sm font-bold text-gray-300">
                      {samplingPct}
                    </td>

                    {/* Created */}
                    <td className="px-8 py-6 text-sm text-gray-500">
                      {ev.created_at
                        ? new Date(ev.created_at).toLocaleDateString()
                        : "-"}
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        </div>
      )}
    </div>
  );
};

export default EvaluatorsTable;
