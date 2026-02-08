import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

// Page Imports
import Dashboard from "./pages/Dashboard";
import Traces from "./pages/Traces";
import Evaluators from "./pages/Evaluators";
import Sessions from "./pages/Sessions";
import Alerts from "./pages/Alerts";
import Datasets from "./pages/Datasets";
import Annotations from "./pages/Annotations";
import Audit from "./pages/Audit";
import Settings from "./pages/Settings";
import Prompts from "./pages/Prompts";
import CreateTemplate from "./pages/CreateTemplate";




// ⭐ ADD THIS IMPORT
import CreateEvaluator from "./pages/CreateEvaluator";

import Sidebar from "./components/Sidebar";

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-[#0e1117] text-[#e0e0e0] overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-[1400px] mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/sessions" element={<Sessions />} />
              <Route path="/traces" element={<Traces />} />

              <Route path="/evaluators" element={<Evaluators />} />

              <Route path="/evaluators/new" element={<CreateEvaluator />} />
              <Route path="/templates/new" element={<CreateTemplate />} />
              <Route path="/annotations" element={<Annotations />} />
              <Route path="/prompts" element={<Prompts />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/datasets" element={<Datasets />} />
              <Route path="/audit" element={<Audit />} />
              <Route path="/settings" element={<Settings />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
