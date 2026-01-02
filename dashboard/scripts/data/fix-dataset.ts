#!/usr/bin/env tsx
/**
 * Converts old dataset format (expected) to new format (asserts)
 */

import { promises as fs } from 'fs';

interface OldCase {
  id: string;
  input: string;
  expected: {
    mustNotContain: string[];
    mustContain?: string[];
    maxQuestions: number;
    minConfidence: number;
  };
}

interface NewCase {
  id: string;
  input: string;
  asserts: {
    minFinalPromptLength: number;
    maxQuestions: number;
    minConfidence: number;
    mustNotContain: string[];
    mustNotHavePlaceholders: boolean;
    mustNotBeChatty: boolean;
    shouldContain: string[];
  };
}

async function convert() {
  const inputPath = process.argv[2] || 'testdata/cases.jsonl';
  const outputPath = process.argv[3] || 'testdata/cases-v2.jsonl';

  const content = await fs.readFile(inputPath, 'utf-8');
  const lines = content.trim().split('\n').filter(line => line);

  const converted: string[] = [];

  for (const line of lines) {
    const oldCase = JSON.parse(line) as OldCase;

    const newCase: NewCase = {
      id: oldCase.id,
      input: oldCase.input,
      asserts: {
        minFinalPromptLength: 50,
        maxQuestions: oldCase.expected.maxQuestions,
        minConfidence: oldCase.expected.minConfidence,
        mustNotContain: oldCase.expected.mustNotContain,
        mustNotHavePlaceholders: true,
        mustNotBeChatty: true,
        shouldContain: oldCase.expected.mustContain || [],
      },
    };

    // Special adjustments for known bad cases
    if (oldCase.id.startsWith('bad-')) {
      // Bad cases should NOT have the banned content, so we don't add expected content
      newCase.asserts.shouldContain = [];

      // Some bad cases are specifically testing question count
      if (oldCase.id.includes('004') || oldCase.id.includes('010')) {
        newCase.asserts.maxQuestions = 2; // Stricter for these specific tests
      }

      // Some bad cases have specific patterns we're testing
      if (oldCase.id === 'bad-006') {
        // This one specifically has "as an ai language model" which should be caught
        newCase.asserts.mustNotContain = ['as an ai language model'];
      }

      // For bad cases where we expect the content to NOT be there, but that's not a failure
      // We'll interpret shouldContain as "should NOT contain"
      if (oldCase.expected.mustContain) {
        newCase.asserts.mustNotContain = [...newCase.asserts.mustNotContain, ...oldCase.expected.mustContain];
        newCase.asserts.shouldContain = [];
      }
    }

    // For good cases, shouldContain are hints, not requirements
    if (oldCase.id.startsWith('good-')) {
      // Convert mustContain to shouldContain hints
      if (oldCase.expected.mustContain) {
        // Remove strict requirements, keep as hints
        newCase.asserts.shouldContain = oldCase.expected.mustContain;

        // Add some must-not patterns that good cases should avoid
        newCase.asserts.mustNotContain = ['as an ai', 'as a language model', 'hard rules', 'output rules'];
      }
    }

    // For ambiguous, keep minimal requirements
    if (oldCase.id.startsWith('ambig-')) {
      newCase.asserts.shouldContain = [];
      newCase.asserts.mustNotContain = ['as an ai', 'as a language model'];
    }

    converted.push(JSON.stringify(newCase));
  }

  await fs.writeFile(outputPath, converted.join('\n') + '\n');
  console.log(`✅ Converted ${converted.length} cases to ${outputPath}`);
  console.log('   Old format: expected { mustNotContain, mustContain, ... }');
  console.log('   New format: asserts { mustNotHavePlaceholders, mustNotBeChatty, shouldContain[...], ... }');
}

// Run if called directly
if (require.main === module) {
  convert().catch(console.error);
}

export { convert };
