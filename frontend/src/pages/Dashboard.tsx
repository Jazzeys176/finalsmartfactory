import React, { useEffect, useState } from "react";
import {
  Activity,
  DollarSign,
  Database,
  Clock,
  ThumbsUp,
  CheckCircle2,
  MessageSquare,
  ShieldAlert,
  AlertTriangle,
  Users,
} from "lucide-react";

import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

import { api } from "../api/client";

/* ================= KPI Card ================= */
const KPICard = ({ title, value, subtitle, icon: Icon }: any) => (
  <div className="bg-[#161a23] border border-gray-800 rounded-xl p-5 flex justify-between">
    <div>
      <p className="text-sm text-gray-400">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
    <Icon className="text-teal-400" />
  </div>
);

/* ================= Empty State ================= */
const EmptyState = ({ text }: { text: string }) => (
  <div className="h-[260px] flex items-center justify-center text-gray-500 text-sm">
    {text}
  </div>
);

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/dashboard/metrics")
      .then((res) => setMetrics(res.data))
      .catch(() => setMetrics(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-6 text-gray-400">Loading dashboard…</div>;
  }

  if (!metrics) {
    return <div className="p-6 text-red-400">Metrics unavailable</div>;
  }

  /* ================= Normalize real data ================= */

  const tracesByName = Object.entries(metrics.trace_count_by_name ?? {}).map(
    ([name, count]) => ({ name, count: Number(count) })
  );

  const costByModel = Object.entries(metrics.cost_by_model ?? {}).map(
    ([name, cost]) => ({ name, cost: Number(cost) })
  );

  const evaluationScores = Object.entries(metrics.evaluation_summary ?? {}).map(
    ([name, v]: any) => ({
      name,
      count: v.count,
      average: Number(v.avg_score).toFixed(3),
    })
  );

  const modelUsage = Object.entries(metrics.tokens_by_model ?? {}).map(
    ([name, tokens]) => ({
      name,
      tokens: Number(tokens),
      cost: Number(metrics.cost_by_model?.[name] ?? 0),
    })
  );

  // Transform daily_users data for LineChart
  // Expects metrics.daily_users as { "2026-03-01": 5, "2026-03-02": 8 } or similar
  // If only total_users exists, create a single point for today
  const dailyActiveUsers = (() => {
    const dailyData = metrics.daily_users ?? {};
    const entries = Object.entries(dailyData);

    if (entries.length > 0) {
      return entries
        .map(([date, users]) => ({
          name: new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          users: Number(users),
          fullDate: date,
        }))
        .sort((a, b) => new Date(a.fullDate).getTime() - new Date(b.fullDate).getTime());
    }

    // Fallback: if we have total_users but no daily breakdown, show as single point using generated_at
    if (metrics.total_users !== undefined && metrics.total_users !== null) {
      const snapshotDate = metrics.generated_at ? new Date(metrics.generated_at) : new Date();
      return [{
        name: snapshotDate.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        users: Number(metrics.total_users),
        fullDate: snapshotDate.toISOString().split('T')[0],
      }];
    }

    return [];
  })();

  return (
    <div className="space-y-8 text-white">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-gray-400 text-sm">
          LLM observability and monitoring
        </p>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Traces"
          value={metrics.total_traces}
          subtitle="Last 7 days"
          icon={Activity}
        />
        <KPICard
          title="Total Cost"
          value={`$${metrics.total_cost.toFixed(4)}`}
          subtitle="API costs"
          icon={DollarSign}
        />
        <KPICard
          title="Total Tokens"
          value={metrics.total_tokens.toLocaleString()}
          subtitle="Input + Output"
          icon={Database}
        />
        <KPICard
          title="Avg Latency"
          value={`${Math.round(metrics.avg_latency_ms)}ms`}
          subtitle="Per trace"
          icon={Clock}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="User Satisfaction" value="NA" subtitle="Insufficient data" icon={ThumbsUp} />
        <KPICard title="Task Completion" value="NA" subtitle="Insufficient data" icon={CheckCircle2} />
        <KPICard title="First Response Accuracy" value="NA" subtitle="Insufficient data" icon={MessageSquare} />
        <KPICard title="Escalation Rate" value="NA" subtitle="Insufficient data" icon={ShieldAlert} />
      </div>

      {/* Drift Detection */}
      <div className="bg-[#1b1f2a] border border-yellow-700/50 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2 text-yellow-400">
          <AlertTriangle />
          <h3 className="font-bold text-lg">Drift Detection Alert</h3>
        </div>
        <p className="text-sm text-gray-300">
          Insufficient historical data to compute drift metrics.
        </p>
      </div>

      {/* Daily Active Users + Response Quality (SAME ROW) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#161a23] border border-gray-800 rounded-xl p-6">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <Activity size={18} className="text-gray-400" />
            Daily Active Users
          </h3>
          {dailyActiveUsers.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={dailyActiveUsers}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
                <XAxis
                  dataKey="name"
                  stroke="#9ca3af"
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                />
                <YAxis
                  stroke="#9ca3af"
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  domain={[0, (dataMax: number) => Math.max(dataMax * 2, dataMax + 3)]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    borderColor: '#334155',
                    color: '#f1f5f9',
                    borderRadius: '8px'
                  }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
                <Line
                  type="monotone"
                  dataKey="users"
                  stroke="#2dd4bf"
                  strokeWidth={3}
                  dot={{ r: 6, fill: '#2dd4bf', strokeWidth: 0 }}
                  activeDot={{ r: 8, fill: '#2dd4bf' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="Insufficient data to display user metrics" />
          )}
        </div>

        <div className="bg-[#161a23] border border-gray-800 rounded-xl p-6">
          <h3 className="font-bold mb-4">Response Quality</h3>
          <EmptyState text="No quality distribution data available" />
        </div>
      </div >

      {/* User Feedback */}
      < div className="bg-[#161a23] border border-gray-800 rounded-xl p-6" >
        <h3 className="font-bold mb-4">User Feedback Summary</h3>
        <EmptyState text="Feedback ingestion not enabled" />
      </div >

      {/* Charts */}
      < div className="grid grid-cols-1 lg:grid-cols-2 gap-6" >
        <div className="bg-[#161a23] border border-gray-800 rounded-xl p-6">
          <h3 className="font-bold mb-4">Traces by Name</h3>
          {tracesByName.length > 0 ? (
            <ResponsiveContainer height={260}>
              <BarChart data={tracesByName}>
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip />
                <Bar dataKey="count" fill="#2dd4bf" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No trace data available" />
          )}
        </div>

        <div className="bg-[#161a23] border border-gray-800 rounded-xl p-6">
          <h3 className="font-bold mb-4">Cost by Model</h3>
          {costByModel.length > 0 ? (
            <ResponsiveContainer height={260}>
              <BarChart data={costByModel}>
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip />
                <Bar dataKey="cost" fill="#2dd4bf" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No cost data available" />
          )}
        </div>
      </div >

      {/* Evaluation Scores Summary */}
      < div className="bg-[#161a23] border border-gray-800 rounded-xl p-6" >
        <h3 className="font-bold mb-4">Evaluation Scores Summary</h3>
        {
          evaluationScores.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="text-left py-2">Score Name</th>
                  <th className="text-right py-2">Count</th>
                  <th className="text-right py-2">Average</th>
                </tr>
              </thead>
              <tbody>
                {evaluationScores.map((s) => (
                  <tr key={s.name} className="border-b border-gray-800">
                    <td className="py-2 text-left">{s.name}</td>
                    <td className="py-2 text-right">{s.count}</td>
                    <td className="py-2 text-right">{s.average}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState text="No evaluation data available" />
          )
        }
      </div >

      {/* Model Usage Details */}
      < div className="bg-[#161a23] border border-gray-800 rounded-xl p-6" >
        <h3 className="font-bold mb-4">Model Usage Details</h3>
        {
          modelUsage.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="text-left py-2">Model</th>
                  <th className="text-right py-2">Tokens</th>
                  <th className="text-right py-2">Cost (USD)</th>
                </tr>
              </thead>
              <tbody>
                {modelUsage.map((m) => (
                  <tr key={m.name} className="border-b border-gray-800">
                    <td className="py-2 text-left">{m.name}</td>
                    <td className="py-2 text-right">{m.tokens.toLocaleString()}</td>
                    <td className="py-2 text-right">${m.cost.toFixed(5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState text="No model usage data available" />
          )
        }
      </div >
    </div >
  );
};

export default Dashboard;
