import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface Trace {
  trace_id: string;
  session_id: string;
  timestamp: string;
  question: string;         // Backend returns this
  input?: string;          // Optional alias
  latency_ms: number;      // Backend returns this
  latency?: number;        // Optional alias
  tokens: number;
  cost: number;
  scores?: Record<string, number>; // Backend returns this
  [key: string]: any;      // Allow loose indexing for other fields like context, answer
}

export interface Session {
  session_id: string;
  user: string; // Backend sends "user"
  user_id?: string; // Frontend alias if needed
  trace_count: number;
  total_tokens: number;
  total_cost: number;
  created_at: string;
}

export interface Evaluator {
  evaluator_id: string;
  name: string;
  active: boolean; // active
  template_id: string; // template
  score_name: string;
  target: string;
  sampling: number;
  created_at: string;
}

export interface Template {
  template_id: string;
  name: string; // Changed from template_name
  template_name?: string; // Optional legacy field
  description: string;
  template: string; // This key is "template" in JSON
  model: string;
  inputs: string[]; // Changed from input_variables
  input_variables?: string[]; // Optional legacy field
  version: string;
  updated_at: string; // Changed from last_updated
  last_updated?: string; // Optional legacy field
}

export interface EvaluationLog {
  timestamp: string;
  evaluator_name: string;
  trace_id: string;
  score: number;
  duration: number;
  status: string;
}
