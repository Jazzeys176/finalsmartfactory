import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronLeft } from "lucide-react";
import { api } from "../api/client";
import { useNavigate } from "react-router-dom";

const CreateEvaluator: React.FC = () => {
  const navigate = useNavigate();

  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // BASIC INFO
  const [name, setName] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
  const [showTemplateMenu, setShowTemplateMenu] = useState(false);
  const [enabled, setEnabled] = useState(true);

  // TARGET TYPE
  const [targetType, setTargetType] = useState<"traces" | "dataset">("traces");

  // VARIABLE MAPPING
  const [variableMapping, setVariableMapping] = useState<
    { variable: string; source: string }[]
  >([]);

  // EXECUTION SETTINGS
  const [samplingRate, setSamplingRate] = useState(100);
  const [delaySeconds, setDelaySeconds] = useState(0);

  /** LOAD TEMPLATES */
  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/templates");
        setTemplates(res.data.templates || []);
      } catch {
        setTemplates([]);
      }
      setLoading(false);
    })();
  }, []);

  /** When template selected → generate mapping inputs */
  useEffect(() => {
    if (!selectedTemplate) return;

    const inputs = selectedTemplate.inputs || [];
    setVariableMapping(
      inputs.map((v: string) => ({
        variable: v,
        source: "",
      }))
    );
  }, [selectedTemplate]);

  /** CREATE EVALUATOR */
  const handleCreate = async () => {
    if (!selectedTemplate) return alert("Select a template first.");
    if (!name.trim()) return alert("Enter evaluator name.");

    const payload = {
      score_name: name.trim(),
      template: {
        id: selectedTemplate.template_id,
        model: selectedTemplate.model,
        prompt_version: "v1",
      },
      status: enabled ? "enabled" : "disabled",
      target: targetType,
      variable_mapping: Object.fromEntries(
        variableMapping.map((m) => [m.variable, m.source])
      ),
      execution: {
        sampling_rate: samplingRate / 100,
        delay_ms: delaySeconds * 1000,
      },
    };

    await api.post("/evaluators", payload);

    alert("Evaluator created!");
    navigate("/evaluators");
  };

  if (loading) {
    return <div className="text-white p-10">Loading templates...</div>;
  }

  return (
    <div className="flex justify-center bg-[#0e1117] text-white min-h-screen p-10">

      {/* MAIN CONTAINER — 60% WIDTH */}
      <div className="w-full max-w-[60vw] space-y-10">

        {/* BACK BUTTON + TITLE */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/evaluators")}
            className="
              flex items-center justify-center
              w-10 h-10 rounded-lg 
              bg-[#161a23] border border-[#1f242d]
              text-gray-300 hover:text-black
              hover:bg-[#13bba4] hover:border-transparent
              transition-all duration-200
            "
          >
            <ChevronLeft size={21} strokeWidth={2.8} />
          </button>

          <div>
            <h1 className="text-3xl font-bold">Create Evaluator</h1>
            <p className="text-gray-400 text-sm">
              Configure an automated evaluation task
            </p>
          </div>
        </div>

        {/* ===================== BASIC INFORMATION ===================== */}
        <section className="bg-[#161a23] border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Basic Information</h2>

          <div className="grid grid-cols-2 gap-6">

            {/* Evaluator Name */}
            <div className="flex flex-col">
              <label className="text-sm text-gray-400 mb-2">
                Evaluator Name
              </label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Hallucination Score"
                className="bg-[#0e1117] border border-gray-800 rounded-lg px-4 py-2 text-sm"
              />
            </div>

            {/* Template Dropdown */}
            <div className="flex flex-col">
              <label className="text-sm text-gray-400 mb-2">Template</label>

              <div className="relative">
                <button
                  onClick={() => setShowTemplateMenu((p) => !p)}
                  className="w-full flex justify-between items-center bg-[#0e1117] border border-gray-800 rounded-lg px-4 py-2 text-sm"
                >
                  {selectedTemplate ? selectedTemplate.name : "Select template"}
                  <ChevronDown size={16} />
                </button>

                {showTemplateMenu && (
                  <div className="absolute mt-1 w-full bg-[#161a23] border border-gray-800 rounded-xl shadow-lg z-50">
                    {templates.map((t) => (
                      <button
                        key={t.template_id}
                        onClick={() => {
                          setSelectedTemplate(t);
                          setShowTemplateMenu(false);
                        }}
                        className="block w-full text-left px-4 py-2 hover:bg-[#1c212e] text-sm"
                      >
                        {t.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enabled Switch */}
          <div className="flex items-center gap-3 mt-6">
            <span className="text-gray-400 text-sm">Enabled</span>

            <button
              onClick={() => setEnabled(!enabled)}
              className={`relative w-12 h-6 rounded-full transition ${
                enabled ? "bg-[#13bba4]" : "bg-gray-700"
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-4 h-4 bg-black rounded-full transition ${
                  enabled ? "translate-x-6" : ""
                }`}
              />
            </button>
          </div>
        </section>

        {/* ===================== TARGET SECTION ===================== */}
        <section className="bg-[#161a23] border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Target Configuration</h2>

          <div className="flex gap-3">
            <button
              onClick={() => setTargetType("traces")}
              className={`px-5 py-2 rounded-lg font-bold text-sm ${
                targetType === "traces"
                  ? "bg-[#13bba4] text-black"
                  : "bg-[#0e1117] text-gray-400 border border-gray-800"
              }`}
            >
              Traces
            </button>

            <button
              onClick={() => setTargetType("dataset")}
              className={`px-5 py-2 rounded-lg font-bold text-sm ${
                targetType === "dataset"
                  ? "bg-[#13bba4] text-black"
                  : "bg-[#0e1117] text-gray-400 border border-gray-800"
              }`}
            >
              Dataset
            </button>
          </div>
        </section>

        {/* ===================== VARIABLE MAPPING ===================== */}
        <section className="bg-[#161a23] border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Variable Mapping</h2>

          {variableMapping.map((m, idx) => (
            <div key={idx} className="grid grid-cols-2 gap-6 mb-4">
              <div className="flex items-center">
                <span className="text-[#13bba4] font-mono text-sm">
                  {`{{${m.variable}}}`}
                </span>
              </div>

              <select
                value={m.source}
                onChange={(e) => {
                  const updated = [...variableMapping];
                  updated[idx].source = e.target.value;
                  setVariableMapping(updated);
                }}
                className="bg-[#0e1117] border border-gray-800 rounded-lg px-4 py-2 text-sm"
              >
                <option value="">Select field</option>
                <option value="trace.input">trace.input</option>
                <option value="trace.output">trace.output</option>
                <option value="span.retrieval.documents">
                  span.retrieval.documents
                </option>
              </select>
            </div>
          ))}
        </section>

        {/* ===================== EXECUTION SETTINGS ===================== */}
        <section className="bg-[#161a23] border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Execution Settings</h2>

          {/* Sampling Rate */}
          <div className="mb-6">
            <label className="text-sm text-gray-400 mb-2 block">
              Sampling Rate
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={samplingRate}
              onChange={(e) => setSamplingRate(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-right text-sm text-gray-300">
              {samplingRate}%
            </div>
          </div>

          {/* Delay */}
          <div>
            <label className="text-sm text-gray-400 mb-2 block">
              Execution Delay
            </label>
            <input
              type="range"
              min={0}
              max={30}
              value={delaySeconds}
              onChange={(e) => setDelaySeconds(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-right text-sm text-gray-300">
              {delaySeconds}s
            </div>
          </div>
        </section>

        {/* ===================== BUTTONS ===================== */}
        <div className="flex justify-end gap-4 pb-10">
          <button
            onClick={() => navigate("/evaluators")}
            className="px-6 py-2 bg-[#13161d] text-gray-300 border border-gray-700 rounded-lg hover:bg-[#191e28]"
          >
            Cancel
          </button>

          <button
            onClick={handleCreate}
            className="px-6 py-2 bg-[#13bba4] text-black rounded-lg font-black hover:bg-[#0fae98]"
          >
            Create Evaluator
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateEvaluator;
