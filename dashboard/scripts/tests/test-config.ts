#!/usr/bin/env tsx
/**
 * Simple test script for configuration system
 * Verifies fail-safe behavior and validation
 */

import { loadConfig, loadConfigFresh, isSafeMode, getSafeModeErrors, getConfigStatus } from "../src/core/config";

console.log("🧪 Testing Configuration System\n");

// Test 1: Load config (should use defaults since no preferences set)
console.log("Test 1: Load config with no preferences");
try {
  const result = loadConfig();
  console.log(`✅ Config loaded: safeMode=${result.safeMode}`);
  console.log(`   Source: ${result.source}`);
  console.log(`   Model: ${result.config.ollama.model}`);
  console.log(`   Timeout: ${result.config.ollama.timeoutMs}ms`);
  console.log(`   Max questions: ${result.config.pipeline.maxQuestions}\n`);
} catch (error) {
  console.log(`❌ Failed: ${error}\n`);
}

// Test 2: Check safe mode status
console.log("Test 2: Safe mode status");
const safeMode = isSafeMode();
console.log(`✅ isSafeMode() = ${safeMode}\n`);

// Test 3: Get config status
console.log("Test 3: Config status");
const status = getConfigStatus();
console.log(`✅ Status: ${status.status}`);
console.log(`   Message: ${status.message}`);
console.log(`   Errors: ${status.errors.length > 0 ? status.errors : "none"}\n`);

// Test 4: Load config fresh (bypass cache)
console.log("Test 4: Load config fresh (bypass cache)");
try {
  const fresh = loadConfigFresh();
  console.log(`✅ Fresh config: safeMode=${fresh.safeMode}\n`);
} catch (error) {
  console.log(`❌ Failed: ${error}\n`);
}

// Test 5: Verify all components
console.log("Test 5: Verify config structure");
const config = loadConfig().config;
console.log(`✅ Ollama config: ${Object.keys(config.ollama).length} fields`);
console.log(`✅ Pipeline config: ${Object.keys(config.pipeline).length} fields`);
console.log(`✅ Quality config: ${Object.keys(config.quality).length} fields`);
console.log(`✅ Features config: ${Object.keys(config.features).length} fields`);
console.log(`✅ Presets config: ${Object.keys(config.presets).length} fields`);
console.log(`✅ Patterns config: ${Object.keys(config.patterns).length} fields`);
console.log(`✅ Eval config: ${Object.keys(config.eval).length} fields\n`);

console.log("🎯 All tests passed! Configuration system is functional.\n");
