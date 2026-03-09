import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  Clock,
  ClipboardCheck,
  ListTodo,
  MessageSquare,
  Database,
  AlertTriangle,
  FileText,
  Settings
} from 'lucide-react';

export default function Sidebar() {
  const { pathname } = useLocation();

  const menu = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Tracing", path: "/traces", icon: Activity },
    { name: "Sessions", path: "/sessions", icon: Clock },
    { name: "Evaluators", path: "/evaluators", icon: ClipboardCheck },
    { name: "Annotation Queues", path: "/annotations", icon: ListTodo },
    { name: "Prompts", path: "/prompts", icon: MessageSquare },
    { name: "Datasets", path: "/datasets", icon: Database },
    { name: "Alerts", path: "/alerts", icon: AlertTriangle },
    { name: "Audit", path: "/audit", icon: FileText },
    { name: "Settings", path: "/settings", icon: Settings },
  ];

  return (
    <div className="w-64 bg-[#11141d] text-[#8e9196] h-screen flex flex-col border-r border-[#1e2330]">
      <div className="p-4 border-b border-[#1e2330] flex items-center gap-2 text-xs font-medium cursor-pointer hover:text-white">
        <span>🏠</span>
        <span>&lt; All Use Cases</span>
      </div>

      <div className="p-6">
        <h1 className="text-[#4db6ac] text-xl font-bold leading-tight">
          Smart Factory AI
        </h1>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] text-[#8e9196] uppercase font-semibold">
            LLMOps Platform
          </span>
          <span className="bg-[#2a2d37] text-white text-[10px] px-1.5 py-0.5 rounded font-bold">
            PROD
          </span>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-1 mt-4">
        {menu.map((item) => {
          const isActive =
            pathname === item.path ||
            (item.path === "/Dashboard" && pathname === "/");

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${isActive
                ? "bg-[#4db6ac] text-black shadow-lg hover:bg-[#4db6ac] hover:text-black font-semibold"
                : "text-white hover:bg-[#1e2330] hover:text-white"
                }`}
            >
              <span className="text-lg"><item.icon className="w-5 h-5" /></span>
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
