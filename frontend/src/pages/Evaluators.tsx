import React, { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

import {
  api,
  type Evaluator,
  type Template,
  type EvaluationLog,
  type Trace,
} from "../api/client";

import EvaluatorsTable from "../components/EvaluatorsTable";
import TemplatesList from "../components/TemplatesList";
import LogsTable from "../components/LogsTable";
import TraceModal from "../components/TraceModal";

const EvaluatorsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [evaluators, setEvaluators] = useState<Evaluator[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [logs, setLogs] = useState<EvaluationLog[]>([]);
  const [loading, setLoading] = useState(true);

  // ✅ Initialize tab from navigation state
  const [activeTab, setActiveTab] =
    useState<"evaluators" | "templates" | "logs">(
      (location.state as any)?.tab ?? "evaluators"
    );

  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [loadingTrace, setLoadingTrace] = useState(false);

  const [filterEvaluator, setFilterEvaluator] = useState("All Evaluators");
  const [filterStatus, setFilterStatus] = useState("All Status");
  const [showEvaluatorDropdown, setShowEvaluatorDropdown] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);

  // ✅ Sync tab if navigation state changes (back/forward, redirects)
  useEffect(() => {
    const tab = (location.state as any)?.tab;
    if (tab) setActiveTab(tab);
  }, [location.state]);

  /** Filter logs */
  const filteredLogs = logs.filter((log) => {
    const evalMatch =
      filterEvaluator === "All Evaluators" ||
      log.evaluator_name === filterEvaluator;

    const status = (log.status || "").toLowerCase();
    const statusMatch =
      filterStatus === "All Status" ||
      status === filterStatus.toLowerCase();

    return evalMatch && statusMatch;
  });

  /** Fetch all data */
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);

    try {
      const res = await api.get("/evaluators");
      setEvaluators(Array.isArray(res.data) ? res.data : []);
    } catch {
      setEvaluators([]);
    }

    try {
      const res = await api.get("/templates");
      const t = res.data;
      if (t?.templates) setTemplates(t.templates);
      else if (Array.isArray(t)) setTemplates(t);
      else setTemplates([]);
    } catch {
      setTemplates([]);
    }

    try {
      const res = await api.get("/evaluations");
      setLogs(Array.isArray(res.data) ? res.data : []);
    } catch {
      setLogs([]);
    }

    setLoading(false);
  };

  /** View trace modal */
  const handleViewTrace = async (traceId: string) => {
    if (!traceId) return;
    setLoadingTrace(true);

    try {
      const res = await api.get(`/traces/${traceId}`);
      setSelectedTrace(res.data);
    } finally {
      setLoadingTrace(false);
    }
  };

  /** Loading screen */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-[#13bba4]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-currentColor" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#0e1117] text-white p-8">

      {/* HEADER */}
      <div className="flex justify-between items-start mb-10">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Evaluators</h1>
          <p className="text-gray-400 text-sm">Automated evaluation system</p>
        </div>

        {/* NEW EVALUATOR */}
        <button
          onClick={() => navigate("/evaluators/new")}
          className="flex items-center gap-2 px-5 py-2.5 bg-[#13bba4] text-black font-black rounded-lg"
        >
          <Plus size={18} strokeWidth={3} />
          New Evaluator
        </button>
      </div>

      {/* TABS */}
      <div className="flex gap-1 p-1 bg-gray-900/50 rounded-xl w-fit border border-gray-800 mb-10">
        {(["evaluators", "templates", "logs"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-2 rounded-lg text-xs font-bold capitalize ${
              activeTab === tab ? "bg-[#1c212e] text-white" : "text-gray-500"
            }`}
          >
            {tab === "logs" ? "Evaluation Log" : tab}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      {activeTab === "evaluators" && (
        <EvaluatorsTable evaluators={evaluators} />
      )}

      {activeTab === "templates" && (
        <TemplatesList
          templates={templates}
          onNewTemplate={() => navigate("/templates/new")}
        />
      )}

      {activeTab === "logs" && (
        <LogsTable
          logs={logs}
          filteredLogs={filteredLogs}
          filterEvaluator={filterEvaluator}
          setFilterEvaluator={setFilterEvaluator}
          filterStatus={filterStatus}
          setFilterStatus={setFilterStatus}
          showEvaluatorDropdown={showEvaluatorDropdown}
          setShowEvaluatorDropdown={setShowEvaluatorDropdown}
          showStatusDropdown={showStatusDropdown}
          setShowStatusDropdown={setShowStatusDropdown}
          handleViewTrace={handleViewTrace}
        />
      )}

      {/* TRACE MODAL */}
      {(selectedTrace || loadingTrace) && (
        <TraceModal
          selectedTrace={selectedTrace}
          loadingTrace={loadingTrace}
          onClose={() => setSelectedTrace(null)}
        />
      )}
    </div>
  );
};

export default EvaluatorsPage;
