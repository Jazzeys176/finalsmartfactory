import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Terminal, FileText } from 'lucide-react';
import { api } from '../api/client';

interface Prompt {
    id: string;
    name: string;
    description: string;
    tags: string[];
    latest_version: number;
}

interface PromptVersion {
    version: number;
    date: string;
    author: string;
    comment: string;
    environment: string;
    content: string;
    variables: string[];
}

const Prompts = () => {
    const navigate = useNavigate();

    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);

    const [content, setContent] = useState("");
    const [variables, setVariables] = useState<string[]>([]);
    const [history, setHistory] = useState<PromptVersion[]>([]);
    const [viewingVersion, setViewingVersion] = useState<number | null>(null);

    useEffect(() => {
        fetchPrompts();
    }, []);

    // 🔹 Normalize backend response
    const fetchPrompts = async () => {
        try {
            const res = await api.get('/api/v1/prompts');

            const data = Array.isArray(res.data) ? res.data : [];

            const normalized: Prompt[] = data.map((p: any) => ({
                id: p.id,
                name: p.name || "",
                description: p.description || "",
                tags: Array.isArray(p.tags) ? p.tags : [],
                latest_version: p.latest_version || p.version || 1
            }));

            setPrompts(normalized);

            if (normalized.length > 0) {
                setSelectedPromptId(normalized[0].id);
            }

        } catch (e) {
            console.error("Failed to fetch prompts", e);
            setPrompts([]);
        }
    };

    useEffect(() => {
        if (!selectedPromptId) return;

        const prompt = prompts.find(p => p.id === selectedPromptId);
        if (prompt) {
            fetchHistory(prompt.name);
        }
    }, [selectedPromptId, prompts]);

    const fetchHistory = async (name: string) => {
        try {
            const res = await api.get(`/api/v1/prompts/${name}/history`);

            const data = Array.isArray(res.data) ? res.data : [];

            const normalized: PromptVersion[] = data.map((ver: any) => ({
                version: ver.version,
                date: ver.date || "",
                author: ver.author || "system",
                comment: ver.comment || `Version ${ver.version}`,
                environment: ver.environment || "dev",
                content: ver.content || "",
                variables: Array.isArray(ver.variables) ? ver.variables : []
            }));

            setHistory(normalized);

            if (normalized.length > 0) {
                const latest = normalized[0];
                setViewingVersion(latest.version);
                setContent(latest.content);
                setVariables(latest.variables);
            }

        } catch (e) {
            console.error("Failed to fetch history", e);
            setHistory([]);
        }
    };

    const handleVersionSelect = (ver: PromptVersion) => {
        setViewingVersion(ver.version);
        setContent(ver.content || "");
        setVariables(ver.variables || []);
    };

    const selectedPrompt = prompts.find(p => p.id === selectedPromptId);

    return (
        <div className="h-[calc(100vh-theme(spacing.20))] flex gap-6 text-slate-200">

            {/* Sidebar */}
            <div className="w-80 flex flex-col gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-100">Prompts</h2>
                    <p className="text-xs text-slate-500">
                        Manage prompt templates and versions
                    </p>
                </div>

                <div className="bg-[#111827] rounded-xl border border-slate-800 flex flex-col overflow-hidden h-full shadow-lg">
                    <div className="p-4 border-b border-slate-800">
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                            Prompt Library
                        </h3>
                    </div>

                    <div className="flex-1 overflow-y-auto p-2 space-y-2">

                        {prompts.length === 0 && (
                            <div className="p-8 text-center text-slate-500 text-sm">
                                No prompts found.
                            </div>
                        )}

                        {prompts.map(p => (
                            <div
                                key={p.id}
                                onClick={() => setSelectedPromptId(p.id)}
                                className={`p-3 rounded-lg cursor-pointer border transition-all ${
                                    selectedPromptId === p.id
                                        ? "bg-slate-800/80 border-teal-500/50"
                                        : "bg-[#0D1117] border-slate-800 hover:bg-slate-800/50"
                                }`}
                            >
                                <div className="flex justify-between mb-1">
                                    <h4 className="font-medium text-sm truncate">
                                        {p.name}
                                    </h4>
                                    <span className="text-[10px] font-mono text-slate-500">
                                        v{p.latest_version}
                                    </span>
                                </div>

                                <p className="text-xs text-slate-500 mb-2">
                                    {p.description}
                                </p>

                                <div className="flex flex-wrap gap-1.5">
                                    {(p.tags || []).map(t => (
                                        <span
                                            key={t}
                                            className="px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-[9px] text-slate-400 uppercase"
                                        >
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}

                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col gap-4 overflow-hidden">

                <div className="flex justify-end h-10">
                    <button
                        onClick={() => navigate('/prompts/new')}
                        className="flex items-center px-3 py-1.5 bg-teal-500 text-slate-950 rounded-lg text-sm font-bold"
                    >
                        <Plus size={16} className="mr-2" />
                        New Prompt
                    </button>
                </div>

                {selectedPrompt ? (
                    <div className="flex-1 bg-[#111827] rounded-xl border border-slate-800 flex flex-col overflow-hidden shadow-xl">

                        <div className="p-6 border-b border-slate-800 flex justify-between">
                            <div className="flex gap-4">
                                <div className="p-3 bg-slate-800 rounded-lg">
                                    <FileText size={20} className="text-slate-400" />
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold">
                                        {selectedPrompt.name}
                                    </h1>
                                    <p className="text-slate-500 text-sm">
                                        {selectedPrompt.description}
                                    </p>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-xs text-slate-500">
                                    Viewing Version
                                </span>
                                <div className="text-xl font-bold">
                                    {viewingVersion ?? "-"}
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 bg-[#0B0E14]">

                            {/* Editor */}
                            <textarea
                                className="w-full h-80 bg-[#0D1117] text-slate-300 font-mono text-sm p-6 resize-none"
                                value={content}
                                readOnly
                            />

                            <div className="mt-4">
                                <h4 className="text-xs text-slate-500 uppercase mb-2">
                                    Variables Detected
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                    {(variables || []).map(v => (
                                        <span
                                            key={v}
                                            className="text-xs text-teal-400 font-mono"
                                        >
                                            {`{{${v}}}`}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* History */}
                            <div className="mt-8 space-y-4">
                                {(history || []).map(ver => (
                                    <div
                                        key={ver.version}
                                        onClick={() => handleVersionSelect(ver)}
                                        className="bg-[#151921] border border-slate-800 rounded-lg p-4 cursor-pointer hover:bg-slate-800/50"
                                    >
                                        <div className="flex justify-between">
                                            <span className="font-bold">
                                                v{ver.version}
                                            </span>
                                            <span className="text-xs text-slate-500">
                                                {ver.date}
                                            </span>
                                        </div>
                                        <div className="text-sm text-slate-400">
                                            {ver.comment}
                                        </div>
                                    </div>
                                ))}
                            </div>

                        </div>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-500 bg-[#111827] rounded-xl border border-slate-800">
                        <Terminal size={48} className="mb-4 opacity-20" />
                        <p>Select a prompt to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Prompts;
