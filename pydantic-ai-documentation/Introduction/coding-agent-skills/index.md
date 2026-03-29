# Coding Agent Skills

If you're building Pydantic AI applications with a coding agent, you can install the Pydantic AI skill from the [`pydantic/skills`](https://github.com/pydantic/skills) repository to give your agent up-to-date framework knowledge.

[Agent skills](https://agentskills.io) are packages of instructions and reference material that coding agents load on demand. With the skill installed, coding agents have access to Pydantic AI patterns, architecture guidance, and common task references covering [tools](https://ai.pydantic.dev/tools/index.md), [capabilities](https://ai.pydantic.dev/capabilities/index.md), [structured output](https://ai.pydantic.dev/output/index.md), [streaming](https://ai.pydantic.dev/agent/#streaming-events-and-final-output), [testing](https://ai.pydantic.dev/testing/index.md), [multi-agent delegation](https://ai.pydantic.dev/multi-agent-applications/index.md), [hooks](https://ai.pydantic.dev/hooks/index.md), and [agent specs](https://ai.pydantic.dev/agent-spec/index.md).

## Installation

### Claude Code

Add the Pydantic marketplace and install the plugin:

```bash
claude plugin marketplace add pydantic/skills
claude plugin install ai@pydantic-skills
```

### Cross-Agent (agentskills.io)

Install the Pydantic AI skill using the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add pydantic/skills
```

This works with 30+ agents via the [agentskills.io](https://agentskills.io) standard, including Claude Code, Codex, Cursor, and Gemini CLI.

## See Also

- [`pydantic/skills`](https://github.com/pydantic/skills): source repository
- [agentskills.io](https://agentskills.io): the open standard for agent skills
