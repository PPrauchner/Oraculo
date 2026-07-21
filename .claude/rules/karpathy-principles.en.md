*[Versão em português](karpathy-principles.md)*

# Behavioural Principles (Karpathy)

Guidelines to reduce common errors in AI coding.
Loaded in every session — applies to any task in the project.

## 1. Think Before You Code

Before implementing anything:
- State your assumptions explicitly. If unsure, ask — do not assume.
- If multiple interpretations are possible, present them; do not choose silently.
- If a simpler approach exists, say so. Question when necessary.
- If something is unclear, stop. Name what is unclear and ask.

## 2. Simplicity First

Write the minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No unrequested "flexibility" or "configurability".
- No error handling for impossible scenarios.
- If you wrote 200 lines and they could be 50, rewrite.

Test: would a senior engineer say it is too complicated? If so, simplify.

## 3. Surgical Changes

Touch only what is necessary. Clean up only your own mess.

When editing existing code:
- Do not "improve" adjacent code, comments or formatting.
- Do not refactor things that are not broken.
- Keep the existing style, even if you would do it differently.
- If you notice unrelated dead code, mention it — do not delete it.

When creating new code that makes something obsolete:
- Remove imports/variables/functions that YOUR changes made unnecessary.
- Do not remove pre-existing dead code unless asked.

Test: every changed line must trace directly to the user's request.

## 4. Goal-Oriented Execution

Define success criteria. Loop until verified.

Turn tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure the tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

Strong criteria allow looping independently. Weak criteria ("make it work") require constant
clarification.
