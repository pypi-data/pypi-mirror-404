# AGENTS.md - Shared Agent Context

This file is read by ALL models (Claude, Codex, Gemini, Local).
Edit once, all agents see the same context.

## Project Context

<!-- Add your project description here -->
Project: [Your Project Name]
Description: [What you're building]

## Current Task

<!-- Updated automatically by Context Bus, or manually -->
Task: [Current task description]
Status: idle | in_progress | blocked | completed

## Key Constraints

<!-- Rules all models should follow -->
- Follow existing code patterns
- Write tests for new features
- Keep functions under 50 lines

## Important Files

<!-- Files that provide context -->
- README.md
- src/main.ts
- docs/architecture.md

## Decisions Made

<!-- Key architectural decisions -->
- Using TypeScript for type safety
- PostgreSQL for database
- JWT for authentication

## Notes for All Models

<!-- Any model reading this should know -->
- Run `npm test` before committing
- Use conventional commits
- Ask before deleting files
