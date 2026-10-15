# Agent instructions

Revision: 1 — 2026-10-15

- This repository is public. Include only generic presentation code, documentation and synthetic tests. Never include private repository names or content, company names/emails, deployment paths, device/chat/user identifiers, credentials, tokens or logs.
- Runtime code uses Python standard library only. Render data; do not open connections, read credentials, start agents, stop processes or change application state.
- Cancellation buttons are presentation only. Consuming applications must validate the caller, chat/topic, message and active task before cancellation.
- Preserve unknown usage as unavailable; never infer model identity, context occupancy or quota from model prose.
- Documents use stable kebab-case names, with revision/date inside. AGENTS.md and README.md are filename exceptions.
- Use human Git identity. Conventional Commits must include verified agent provenance; never invent a model name.
- Validate installed-package imports as well as synthetic unit tests before delivery. A passing render test is not Telegram client acceptance.
