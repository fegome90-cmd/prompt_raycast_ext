/**
 * Types for conversational wizard mode
 * Integrates with NLaC analysis (Intent + Complexity)
 */

export type WizardMode = "auto" | "always" | "off";
export type IntentType = "DEBUG" | "REFACTOR" | "GENERATE" | "ANALYZE";
export type ComplexityLevel = "SIMPLE" | "MODERATE" | "COMPLEX";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
  timestamp: number;
  metadata?: {
    confidence?: number;
    turnNumber: number;
    intent?: IntentType;
    complexity?: ComplexityLevel;
    knnCount?: number;
  };
}

export interface AmbiguityDetection {
  isAmbiguous: boolean;
  confidence: number;
  missingInfo: string[];
  suggestedQuestions: string[];
  intent?: IntentType;
  complexity?: ComplexityLevel;
  knnExamples?: Array<{
    input: string;
    output: string;
    similarity: number;
  }>;
}

export interface WizardConfig {
  mode: WizardMode;
  maxTurns: number;
  currentTurn: number;
  timeoutPerTurn: number;
  adaptiveTurns: boolean;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  inputContext: {
    originalInput: string;
    preset: string;
    source: "dspy" | "ollama";
  };
  wizard: {
    enabled: boolean;
    config: WizardConfig;
    ambiguityScore: number;
    completed: boolean;
    nlacAnalysis?: {
      intent: IntentType;
      complexity: ComplexityLevel;
      confidence: number;
    };
  };
  createdAt: number;
  lastActivity: number;
}
