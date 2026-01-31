---
name: llm-council
description: LLM Council with 5 frontier models (Opus 4.5, GPT-5.2, Gemini 3 Pro, Grok 4, Kimi K2.5). Models deliberate on a question, each seeing previous responses, then a judge synthesizes consensus. Use for important decisions needing diverse AI perspectives.
---

# LLM Council

5 frontier models deliberate on a question. Unlike `/ask-llms` which shows parallel responses, this creates an actual debate where models see and respond to previous speakers, followed by a judge synthesizing the consensus.

## When to Use

- Important decisions that benefit from diverse perspectives
- You want models to actually debate, not just answer in parallel
- You need a synthesized recommendation, not raw comparison
- Exploring trade-offs where different viewpoints matter

## When NOT to Use

- **Thinking out loud** — exploratory discussions where you're still forming the question
- **Claude has good context** — if we've been discussing the topic, direct conversation is faster
- **Personal preference** — council excels at objective trade-offs, not "what would I enjoy"
- **Already converged** — if discussion reached a conclusion, council just validates
- **Speed matters** — takes 60-90s and costs several dollars

## Prerequisites

```bash
export OPENROUTER_API_KEY=sk-or-v1-...    # Required
export GOOGLE_API_KEY=AIza...              # Optional: Gemini fallback
export MOONSHOT_API_KEY=sk-...             # Optional: Kimi fallback
```

## Instructions

### Step 1: Get the Question

Ask the user what question they want the council to deliberate, or use the question they provided.

### Step 2: Run the Council

```bash
llm-council "Should we use microservices or a monolith for this project?"
```

**Common options:**
```bash
llm-council "question" --social              # Interview/networking questions
llm-council "question" --persona "context"   # Add personal context
llm-council "question" --rounds 3            # More deliberation
llm-council "question" --output file.md      # Save transcript
llm-council "question" --share               # Upload to secret Gist
```

### Step 3: Review and Critique

Present the judge's synthesis, then critique it:
- Did the council overcorrect on any point?
- Did they miss obvious scenarios?
- Does the advice fit the user's specific context?
- Any groupthink where everyone agreed too fast?

## Prompting Tips

**For social/conversational contexts** (interview questions, networking, outreach):

LLMs over-optimize for thoroughness. Add constraints like:
- "Make it feel like a natural conversation"
- "Something you'd actually ask over coffee"
- "Simple and human, not structured and comprehensive"

**Match context depth to question type:**
- Strategic decisions: provide rich context (full background, constraints, history)
- Social questions: minimal context + clear tone constraints

**For architecture/design questions:**

Provide scale and constraints upfront to avoid premature optimization advice:
- "This is a single-user system" (avoids multi-user concerns)
- "We have 500 notes, not 50,000" (avoids scaling infrastructure)
- "Manual processes are acceptable" (avoids automation overkill)

Without these constraints, council tends to suggest infrastructure for problems that don't exist yet.

## See Also

- Full documentation: `cat /Users/terry/skills/llm-council/README.md`
- Python API available: `from llm_council import run_council`
