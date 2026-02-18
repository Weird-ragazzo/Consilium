export interface ModelResponse {
  model_name: string;
  model_id: string;
  initial_response: string;
  critique_received: string;
  final_response: string;
  was_revised: boolean;
}

export interface CouncilResponse {
  prompt: string;
  model_a: ModelResponse;
  model_b: ModelResponse;
  phases_completed: string[];
}

export type Phase = "idle" | "generating" | "critiquing" | "revising" | "done" | "error";
