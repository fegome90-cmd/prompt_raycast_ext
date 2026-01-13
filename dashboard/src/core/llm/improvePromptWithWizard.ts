import { SessionManager } from "../conversation/SessionManager";
import type { ChatSession, WizardMode, IntentType, ComplexityLevel } from "../conversation/types";
import { improvePromptWithHybrid, type ImprovePromptPreset } from "./improvePrompt";

// Complexity thresholds for heuristic analysis
const COMPLEXITY_THRESHOLDS = {
  SIMPLE_MAX_WORDS: 10,
  MODERATE_MAX_WORDS: 20,
  LOW_CONFIDENCE_MAX_WORDS: 5,
} as const;

interface WizardOptions {
  rawInput: string;
  preset: ImprovePromptPreset;
  wizardMode: WizardMode;
  maxWizardTurns: number;
  baseUrl: string;
  model: string;
  dspyBaseUrl: string;
  dspyTimeoutMs: number;
  temperature?: number;
  systemPattern?: string;
}

interface NLaCAnalysis {
  intent: IntentType;
  complexity: ComplexityLevel;
  confidence: number;
}

export async function improvePromptWithWizard(options: WizardOptions): Promise<{
  session: ChatSession;
  isComplete: boolean;
  needsClarification: boolean;
}> {
  // Step 1: Analyze input (placeholder for now, will call NLaC backend)
  const nlacAnalysis: NLaCAnalysis = await analyzeInput(options.rawInput);

  // Step 2: Create session
  const session = await SessionManager.createSession(
    options.rawInput,
    options.preset,
    "dspy",
    options.wizardMode,
    options.maxWizardTurns,
    nlacAnalysis,
  );

  // Step 3: If wizard disabled, generate directly
  if (!session.wizard.enabled) {
    try {
      const result = await improvePromptWithHybrid({
        rawInput: options.rawInput,
        preset: options.preset,
        options: {
          baseUrl: options.baseUrl,
          model: options.model,
          timeoutMs: options.dspyTimeoutMs,
          temperature: options.temperature,
          systemPattern: options.systemPattern,
          dspyBaseUrl: options.dspyBaseUrl,
          dspyTimeoutMs: options.dspyTimeoutMs,
        },
      });

      await SessionManager.appendAssistantMessage(session.id, result.improved_prompt, {
        isAmbiguous: false,
        confidence: result.confidence,
      });

      const updatedSession = await SessionManager.getSession(session.id);
      if (!updatedSession) {
        throw new Error(`Session ${session.id} was lost from cache`);
      }
      return { session: updatedSession, isComplete: true, needsClarification: false };
    } catch (error) {
      await SessionManager.deleteSession(session.id);
      throw error;
    }
  }

  // Step 4: Generate clarification questions
  const questions = generateClarificationQuestions(nlacAnalysis);

  const clarificationText =
    `I need clarification on your request:\n\n` +
    questions.map((q, i) => `${i + 1}. ${q}`).join("\n") +
    "\n\nPlease respond to continue, or press Enter to generate with current information.";

  await SessionManager.appendAssistantMessage(session.id, clarificationText, {
    confidence: nlacAnalysis.confidence,
    isAmbiguous: true,
  });

  const updatedSession = await SessionManager.getSession(session.id);
  if (!updatedSession) {
    throw new Error(`Session ${session.id} was lost from cache`);
  }
  return { session: updatedSession, isComplete: false, needsClarification: true };
}

export async function continueWizard(
  sessionId: string,
  userResponse: string,
  options: Omit<WizardOptions, "rawInput" | "wizardMode" | "maxWizardTurns">,
): Promise<{ session: ChatSession; isComplete: boolean; prompt?: string }> {
  const session = await SessionManager.getSession(sessionId);
  if (!session) throw new Error("Session not found");

  // Validate response length
  const trimmedResponse = userResponse.trim();
  if (trimmedResponse.length > 0 && trimmedResponse.length < 3) {
    throw new Error("Response too short - please provide more details or press Enter to skip");
  }

  // Don't count empty responses as turns (user is skipping)
  const isSkipping = trimmedResponse === "";
  if (!isSkipping) {
    await SessionManager.appendUserMessage(sessionId, userResponse);
  }

  if (SessionManager.shouldContinueWizard(session)) {
    const followUp = ["What specific details can you provide?"];
    await SessionManager.appendAssistantMessage(session.id, followUp.join("\n"), {
      confidence: 0.5,
      isAmbiguous: true,
    });

    const updatedSession = await SessionManager.getSession(session.id);
    if (!updatedSession) {
      throw new Error(`Session ${session.id} was lost from cache`);
    }
    return { session: updatedSession, isComplete: false };
  }

  // Generate final prompt
  try {
    const result = await improvePromptWithHybrid({
      rawInput: session.inputContext.originalInput,
      preset: session.inputContext.preset as ImprovePromptPreset,
      options: {
        baseUrl: options.baseUrl,
        model: options.model,
        timeoutMs: options.dspyTimeoutMs,
        temperature: options.temperature,
        systemPattern: options.systemPattern,
        dspyBaseUrl: options.dspyBaseUrl,
        dspyTimeoutMs: options.dspyTimeoutMs,
      },
    });

    await SessionManager.appendAssistantMessage(sessionId, result.improved_prompt, {
      isAmbiguous: false,
      confidence: result.confidence,
    });

    await SessionManager.completeWizard(sessionId);

    const finalSession = await SessionManager.getSession(sessionId);
    if (!finalSession) {
      throw new Error(`Session ${sessionId} was lost from cache`);
    }

    return {
      session: finalSession,
      isComplete: true,
      prompt: result.improved_prompt,
    };
  } catch (error) {
    await SessionManager.deleteSession(sessionId);
    throw error;
  }
}

// Placeholder for NLaC analysis (will call backend in Phase 2)
async function analyzeInput(input: string): Promise<NLaCAnalysis> {
  const trimmed = input.trim();
  if (!trimmed) {
    return { intent: "explain", complexity: "SIMPLE", confidence: 0 };
  }

  const tokenCount = trimmed.split(/\s+/).length;
  const complexity =
    tokenCount < COMPLEXITY_THRESHOLDS.SIMPLE_MAX_WORDS
      ? "SIMPLE"
      : tokenCount < COMPLEXITY_THRESHOLDS.MODERATE_MAX_WORDS
      ? "MODERATE"
      : "COMPLEX";

  // Proper type guards instead of 'as any'
  let intent: IntentType = "explain";
  const lowerInput = trimmed.toLowerCase();
  if (lowerInput.includes("create") || lowerInput.includes("build")) {
    intent = "generate";
  } else if (lowerInput.includes("debug") || lowerInput.includes("fix")) {
    intent = "debug";
  } else if (lowerInput.includes("refactor") || lowerInput.includes("improve")) {
    intent = "refactor";
  }

  const confidence = tokenCount < COMPLEXITY_THRESHOLDS.LOW_CONFIDENCE_MAX_WORDS ? 0.4 : 0.8;

  return { intent, complexity, confidence };
}

function generateClarificationQuestions(analysis: NLaCAnalysis): string[] {
  if (analysis.intent === "generate") {
    return ["What specific components or features do you need?", "What are the key requirements or constraints?"];
  }
  if (analysis.complexity === "COMPLEX") {
    return ["What is your primary goal or objective?", "Who is the intended audience?"];
  }
  return ["Can you provide more details about what you need?"];
}
