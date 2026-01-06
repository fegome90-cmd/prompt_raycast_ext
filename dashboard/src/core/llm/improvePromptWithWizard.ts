import { SessionManager } from "../conversation/SessionManager";
import type { ChatSession, WizardMode, IntentType, ComplexityLevel } from "../conversation/types";
import { improvePromptWithHybrid, type ImprovePromptPreset } from "./improvePrompt";

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
    nlacAnalysis
  );

  // Step 3: If wizard disabled, generate directly
  if (!session.wizard.enabled) {
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

    await SessionManager.appendAssistantMessage(
      session.id,
      result.improved_prompt,
      { isAmbiguous: false, confidence: result.confidence }
    );

    return { session, isComplete: true, needsClarification: false };
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

  return { session, isComplete: false, needsClarification: true };
}

export async function continueWizard(
  sessionId: string,
  userResponse: string,
  options: Omit<WizardOptions, "rawInput" | "wizardMode" | "maxWizardTurns">
): Promise<{ session: ChatSession; isComplete: boolean; prompt?: string }> {
  const session = SessionManager.getSession(sessionId);
  if (!session) throw new Error("Session not found");

  await SessionManager.appendUserMessage(sessionId, userResponse);

  if (SessionManager.shouldContinueWizard(session)) {
    const followUp = ["What specific details can you provide?"];
    await SessionManager.appendAssistantMessage(session.id, followUp.join("\n"), {
      confidence: 0.5,
      isAmbiguous: true,
    });

    return { session: SessionManager.getSession(sessionId)!, isComplete: false };
  }

  // Generate final prompt
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

  return {
    session: SessionManager.getSession(sessionId)!,
    isComplete: true,
    prompt: result.improved_prompt,
  };
}

// Placeholder for NLaC analysis (will call backend in Phase 2)
async function analyzeInput(input: string): Promise<NLaCAnalysis> {
  // Simple heuristic for now
  const tokenCount = input.split(/\s+/).length;
  const complexity = tokenCount < 10 ? "SIMPLE" : tokenCount < 20 ? "MODERATE" : "COMPLEX";
  const intent = input.toLowerCase().includes("create") || input.toLowerCase().includes("build") ? "GENERATE" : "ANALYZE";
  const confidence = tokenCount < 5 ? 0.4 : 0.8;

  return { intent, complexity, confidence };
}

function generateClarificationQuestions(analysis: NLaCAnalysis): string[] {
  if (analysis.intent === "GENERATE") {
    return ["What specific components or features do you need?", "What are the key requirements or constraints?"];
  }
  if (analysis.complexity === "COMPLEX") {
    return ["What is your primary goal or objective?", "Who is the intended audience?"];
  }
  return ["Can you provide more details about what you need?"];
}
