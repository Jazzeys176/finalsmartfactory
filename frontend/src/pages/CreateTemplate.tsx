import React, { useState } from "react";
import { ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

// =========================================================
// TOAST COMPONENT (Neon Teal + Red Error, Fade Animation)
// =========================================================
const Toast = ({
  message,
  type,
  onClose,
}: {
  message: string;
  type: "success" | "error";
  onClose: () => void;
}) => {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className={`fixed bottom-6 right-6 min-w-[260px] max-w-[360px] px-5 py-3 rounded-xl 
      border shadow-xl backdrop-blur-md animate-fadeIn
      ${
        type === "success"
          ? "bg-[#0e1713] border-[#13bba4] text-[#13bba4]"
          : "bg-[#1b0e0e] border-red-500 text-red-400"
      }
    `}
    >
      <p className="text-sm font-semibold">{message}</p>
    </div>
  );
};

export default function CreateTemplate() {
  const navigate = useNavigate();

  const [templateName, setTemplateName] = useState("");
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [outputType, setOutputType] = useState("numeric");
  const [prompt, setPrompt] = useState("");

  // TOAST STATE
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const clearToast = () => {
    setSuccessMsg("");
    setErrorMsg("");
  };

  // =========================================================
  // CREATE TEMPLATE API CALL
  // =========================================================
  const handleCreate = async () => {
    clearToast();

    if (!templateName.trim() || !prompt.trim()) {
      setErrorMsg("Template name and prompt cannot be empty.");
      return;
    }

    const id = templateName.trim().toLowerCase().replace(/\s+/g, "_");

    const payload = {
      id,
      template_id: id,
      name: templateName,
      version: "1",
      description,
      model,
      inputs: [],
      template: prompt,
      updated_at: new Date().toISOString(),
    };

    try {
      const res = await fetch("http://localhost:8000/templates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to create template");
      }

      setSuccessMsg("Template created successfully!");

      setTimeout(() => {
        navigate("/evaluators", { state: { tab: "templates" } });
      }, 1500);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Error creating template.");
    }
  };

  return (
    <div className="w-full px-10 py-6 text-white space-y-10 min-h-screen bg-[#0e1117] relative">

      {/* BACK BUTTON + TITLE */}
      <div className="flex items-center gap-4">
        <button
          onClick={() =>
            navigate("/evaluators", { state: { tab: "templates" } })
          }
          className="
            flex items-center justify-center
            w-10 h-10 rounded-lg 
            bg-[#161a23] border border-[#1f242d]
            text-white hover:text-black
            hover:bg-[#13bba4] hover:border-transparent
            transition-all duration-200
          "
        >
          <ChevronLeft size={20} strokeWidth={3} />
        </button>

        <div>
          <h1 className="text-2xl font-bold">Create Evaluator Template</h1>
          <p className="text-sm text-gray-400">
            Define evaluation prompts with variable placeholders
          </p>
        </div>
      </div>

      {/* =============================== */}
      {/* 60 / 40 GRID */}
      {/* =============================== */}
      <div className="grid grid-cols-1 lg:grid-cols-[60%_40%] gap-10">

        {/* LEFT (60%) */}
        <div className="space-y-10">

          {/* DETAILS */}
          <div className="bg-[#161a23] border border-[#1f242d] rounded-xl p-6 space-y-6">
            <h2 className="text-xl font-semibold">Template Details</h2>

            <div>
              <label className="text-sm text-gray-300">Template Name</label>
              <input
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g., Hallucination Detection"
                className="mt-1 w-full bg-[#0e1117] border border-gray-800 rounded-lg p-2 text-sm text-gray-200"
              />
            </div>

            <div>
              <label className="text-sm text-gray-300">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of what this template evaluates"
                className="mt-1 w-full bg-[#0e1117] border border-gray-800 rounded-lg p-2 h-20 text-sm text-gray-200"
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="text-sm text-gray-300">Evaluation Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="mt-1 w-full bg-[#0e1117] border border-gray-800 rounded-lg p-2 text-sm text-gray-200"
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4">GPT-4</option>
                </select>
              </div>

              <div>
                <label className="text-sm text-gray-300">Output Type</label>
                <select
                  value={outputType}
                  onChange={(e) => setOutputType(e.target.value)}
                  className="mt-1 w-full bg-[#0e1117] border border-gray-800 rounded-lg p-2 text-sm text-gray-200"
                >
                  <option value="numeric">Numeric (0–1)</option>
                  <option value="binary">Binary (Pass/Fail)</option>
                </select>
              </div>
            </div>
          </div>

          {/* PROMPT */}
          <div className="bg-[#161a23] border border-[#1f242d] rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Evaluation Prompt</h2>
              <span className="text-xs px-2 py-1 bg-gray-800 rounded-md border border-gray-700">
                Use {"{{variable}}"} syntax
              </span>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full bg-[#0e1117] border border-gray-800 rounded-xl p-4 h-72 text-sm text-gray-200 whitespace-pre-wrap"
              placeholder={`Enter your evaluation prompt here.

Use {{variable}} placeholders.

Example:
User Input: {{input}}
AI Response: {{output}}
Context: {{context}}

Evaluate the response and provide a score from 0 to 1.`}
            />
          </div>
        </div>

        {/* RIGHT (40%) */}
        <div className="space-y-6">

          <div className="bg-[#161a23] border border-[#1f242d] rounded-xl p-6">
            <h3 className="font-semibold mb-2">Detected Variables</h3>
            <p className="text-sm text-gray-400">
              No variables detected. Use {"{{variable}}"} syntax in your prompt.
            </p>
          </div>

          <div className="bg-[#161a23] border border-[#1f242d] rounded-xl p-6 text-sm text-gray-300 space-y-2">
            <p>• Be specific about scoring criteria</p>
            <p>• Include edge-case examples</p>
            <p>• Define what each score range means</p>
            <p>• Test with diverse inputs before deploying</p>
          </div>
        </div>
      </div>

      {/* FOOTER BUTTONS */}
      <div className="flex justify-end gap-4 pb-10">
        <button
          onClick={() =>
            navigate("/evaluators", { state: { tab: "templates" } })
          }
          className="px-4 py-2 rounded-lg bg-[#13161d] text-gray-300 border border-gray-700 hover:bg-[#191e28]"
        >
          Cancel
        </button>

        <button
          onClick={handleCreate}
          className="px-5 py-2 rounded-lg font-bold bg-[#13bba4] text-black hover:bg-[#0fae98] transition"
        >
          Create Template
        </button>
      </div>

      {/* TOASTS */}
      {successMsg && (
        <Toast message={successMsg} type="success" onClose={clearToast} />
      )}
      {errorMsg && (
        <Toast message={errorMsg} type="error" onClose={clearToast} />
      )}
    </div>
  );
}
