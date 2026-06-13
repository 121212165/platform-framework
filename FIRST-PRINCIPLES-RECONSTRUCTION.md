# First-Principles Reconstruction: platform-framework

> Applied Elon Musk's first-principles thinking: break to fundamental truths, rebuild from zero.

## Core Problem

A Python/FastAPI mental health chatbot that calls ZhipuAI with a chat web UI.

## First Principles Breakdown

1. The chat interface IS the product.
2. Conversation persistence = append to a JSONL file.
3. The system prompt defines the persona. That is the intellectual property.
4. 70% of the codebase is over-engineering.

## Reconstruction Blueprint

~200 lines of code. Chat UI + LLM API call + JSONL persistence + system prompt.

## Musk\'s Razor

Cut entire dify/ directory, entire mcp/ directory, service manager, RAG pipeline. The irreducible core: one chat page, one API endpoint, one prompt.
