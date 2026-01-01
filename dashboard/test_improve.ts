import { improvePromptWithOllama } from './src/core/llm/improvePrompt.js';

async function test() {
  try {
    console.log("Testing improvePromptWithOllama...");
    console.log("Input: 'write a blog post about AI'");
    console.log("");
    
    const result = await improvePromptWithOllama({
      rawInput: "write a blog post about AI",
      preset: "structured",
      options: {
        baseUrl: "http://localhost:11434",
        model: "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
        timeoutMs: 60000,
        temperature: 0.1
      }
    });
    
    console.log("=== IMPROVED PROMPT ===");
    console.log(result.improved_prompt.substring(0, 500) + "...");
    console.log("");
    console.log("=== METADATA ===");
    console.log("Confidence:", result.confidence);
    console.log("Questions:", result.clarifying_questions);
    console.log("Assumptions:", result.assumptions);
  } catch (error) {
    console.error("Error:", error.message);
    if (error instanceof Error && error.stack) {
      const stack = error.stack.split('\n').slice(0, 5).join('\n');
      console.error("Stack:", stack);
    }
  }
}

test();
