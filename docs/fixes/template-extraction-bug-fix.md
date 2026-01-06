# Template Extraction Bug Fix

## Problem

The FormatConverter was leaving metadata in converted prompts from LangChain Hub. Specifically, prompts like `rlm/rag-prompt` had their `converted.template` field containing the string representation of the LangChain object instead of the clean template:

```json
{
  "template": "input_variables=['context', 'question'] input_types={} partial_variables={} metadata={'lc_hub_owner': 'rlm', 'lc_hub_repo': 'rag-prompt', 'lc_hub_commit_hash': '50442af133e61576e74536c6556cefe1fac147cad032f4377b60c436e6cdcb6e'} messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(...), additional_kwargs={})]"
}
```

## Root Cause

In `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/langchain/fetch_prompts.py`, the `fetch_by_handles()` method was using:

```python
template = prompt_data.template if hasattr(prompt_data, 'template') else str(prompt_data)
```

This worked for simple `PromptTemplate` objects, but for `ChatPromptTemplate` objects, the `.template` attribute returns the `__str__` representation of the object (which includes all metadata) instead of the actual template string.

## Solution

Created a new helper function `_extract_template_from_langchain_object()` that:

1. **Tries direct template attribute first** - For simple `PromptTemplate` objects
2. **Checks ChatPromptTemplate structure** - Extracts from `messages[0].prompt.template`
3. **Uses regex fallback** - Extracts `template="..."` patterns from the string representation
4. **Handles both single and double quotes** - Matches both `template="..."` and `template='...'`
5. **Decodes escape sequences** - Properly handles `\n`, `\t`, `\"`, etc.

## Implementation

### File Modified
- `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/langchain/fetch_prompts.py`

### Changes Made

1. Added `import re` for regex support
2. Created `_extract_template_from_langchain_object()` helper function
3. Updated `fetch_by_handles()` to use the new helper function

## Testing

### Unit Tests
Created `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/test_template_extraction.py` with tests for:
- Simple PromptTemplate extraction
- ChatPromptTemplate extraction
- Dirty template attribute (the bug)
- Prompts with variables

### Verification Scripts
Created two verification scripts:
1. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/verify_fix.py` - Tests fix on existing data
2. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/regenerate_converted.py` - Regenerates converted fields

## Results

### Before Fix
```
rlm/rag-prompt:
  Status: ❌ DIRTY
  Template preview: input_variables=['context', 'question'] input_types={}...
```

### After Fix
```
rlm/rag-prompt:
  Status: ✅ CLEAN
  Template preview: You are an assistant for question-answering tasks.
  Use the following pieces of retrieved context to answer the question...
```

## Impact

- Fixed 2 out of 4 candidates that had dirty templates
- All templates now clean and ready for DSPy format conversion
- Future fetches from LangChain Hub will automatically extract clean templates

## Files Changed

1. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/langchain/fetch_prompts.py` - Main fix
2. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/test_template_extraction.py` - Unit tests
3. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/verify_fix.py` - Verification script
4. `/Users/felipe_gonzalez/Developer/raycast_ext/scripts/tests/langchain/regenerate_converted.py` - Regeneration script
5. `/Users/felipe_gonzalez/Developer/raycast_ext/datasets/exports/langchain-candidates.json` - Fixed data file

## Next Steps

When running `python3 scripts/langchain/import_workflow.py fetch` in the future, the new extraction logic will automatically be used to fetch clean templates from LangChain Hub.
