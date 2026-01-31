---
description: Connect Empathy Framework to Claude Code via MCP. Enable AI workflows, agent coordination, and pattern learning in your IDE.
---

# MCP Integration

Connect Empathy Framework to Claude Desktop or any MCP-compatible client using the Socratic workflow builder.

---

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI applications to external tools and data sources. Empathy Framework exposes its Socratic workflow builder as MCP tools.

---

## Quick Setup

### 1. Install Empathy Framework

```bash
pip install empathy-framework[developer]
```

### 2. Configure Claude Desktop

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
    "mcpServers": {
        "socratic": {
            "command": "python",
            "args": ["-m", "empathy_os.socratic.mcp_server"],
            "env": {
                "ANTHROPIC_API_KEY": "your-api-key-here"
            }
        }
    }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop. You should see the Socratic tools available.

---

## Available Tools

The MCP server exposes 10 tools for building AI workflows through guided conversation:

| Tool | Description |
|------|-------------|
| `socratic_start_session` | Start a new workflow builder session |
| `socratic_set_goal` | Set or update the session goal |
| `socratic_get_questions` | Get clarifying questions |
| `socratic_submit_answers` | Submit answers to questions |
| `socratic_generate_workflow` | Generate the final workflow |
| `socratic_list_sessions` | List all saved sessions |
| `socratic_get_session` | Get details of a session |
| `socratic_list_blueprints` | List saved workflow blueprints |
| `socratic_analyze_goal` | Quick goal analysis without full session |
| `socratic_recommend_agents` | Get agent recommendations |

---

## Example Usage

In Claude Desktop, you can now have conversations like:

> **You:** I want to set up a code review workflow for my Python project

> **Claude:** Let me help you build that. I'll use the Socratic workflow builder to guide you through the process.
>
> *[Uses socratic_start_session and socratic_set_goal]*
>
> I have a few questions to understand your needs better:
> 1. What aspects should the review focus on? (security, performance, style, all)
> 2. How strict should the review be? (lenient, moderate, strict)
> 3. Should it generate fix suggestions automatically?

---

## Manual Testing

Test the MCP server directly:

```bash
# Start the server
python -m empathy_os.socratic.mcp_server

# The server communicates via stdin/stdout using JSON-RPC
# It will respond to MCP protocol messages
```

---

## Troubleshooting

### Server Not Starting

1. Verify Python is in your PATH
2. Check the API key is set correctly
3. Look for errors in Claude Desktop logs

### Tools Not Appearing

1. Restart Claude Desktop completely
2. Verify the config file path is correct
3. Check JSON syntax in config file

### API Key Issues

The server needs `ANTHROPIC_API_KEY` for LLM-powered goal analysis. You can also set it in your shell:

```bash
export ANTHROPIC_API_KEY="your-key"
```

---

## Alternative Clients

The MCP server works with any MCP-compatible client, not just Claude Desktop:

- **Cursor IDE** - Similar configuration approach
- **Custom clients** - Use the MCP SDK to connect
- **CLI testing** - Pipe JSON-RPC messages directly

---

## Next Steps

- [Socratic Tutorial](../tutorials/socratic-tutorial.md) - Deep dive into workflow building
- [Meta-Orchestration](choose-your-path.md#path-3-meta-orchestration) - Advanced multi-agent coordination
- [Python API](../api-reference/index.md) - Direct programmatic access
