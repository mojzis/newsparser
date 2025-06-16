---
author: Oleksii Nikiforov
domain: nikiforovall.blog
evaluation:
  evaluated_at: '2025-06-13T23:09:30.353356Z'
  evaluator: claude-3-haiku-20240307
  is_mcp_related: true
  key_topics:
  - Claude Code
  - AI tool integration
  - Model Context Protocol (MCP)
  - Practical recommendations
  - AI task-based development
  perex: Unleash your AI superpowers with these Claude Code tips - from MCP integration
    to interactive tutoring, this guide has you covered!
  relevance_score: 0.8
  summary: This article provides practical recommendations and best practices for
    using the Claude Code AI tool, including integrating it with external tools and
    data sources via the Model Context Protocol (MCP).
extraction_timestamp: '2025-06-13T23:07:00.298687Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:00.298728Z'
found_in_posts:
- at://did:plc:5trp5aetk54wnndb2e2qlpom/app.bsky.feed.post/3lrj6afkkyc2n
language: en
medium: null
stage: evaluated
title: My Claude Code Usage Best Practices and Recommendations
url: https://nikiforovall.blog/productivity/2025/06/13/claude-code-rules.html
word_count: 457
---

# My Claude Code Usage Best Practices and Recommendations

This post shares my collection of practical recommendations and principles for using Claude Code. For more details and the full source code, check out my repository:

**Source code:** [github.com/NikiforovAll/claude-code-rules](https://github.com/NikiforovAll/claude-code-rules)

* * *

## Practical Recommendations

Here is my list of practical recommendations for using Claude Code:

### Planning

  * Ask Claude to brainstorm ideas and iterate on them. Later, these ideas can be used as grounding context for your prompts.
  * `plan mode` vs `auto-accept mode` vs `edit mode`:
    * Verify what is about to be performed using `plan mode`.
    * Once verified, proceed with `auto-accept mode`.
    * Step-by-step mode is the default mode with no auto-accept.
  * Workflows:
    * a. Explore, plan, code, commit.
    * b. Write tests, commit; code, iterate, commit.
    * c. Write code, screenshot results, iterate.
  * Ask “think hard” to trigger deep thinking:
    * “think” < “think hard” < “think harder” < “ultrathink”

#### AI Task-Based Development

  * Write a plan to an external source \(e.g., file - plan.md\) and use it as a checklist.
  * `plan.prompt.md` \- use an external file as memory for task management and planning.

I’ve created a set of commands to help with AI task-based development:

  * Use `/create-prd` to create a Product Requirements Document \(PRD\) based on user input.
  * Use `/generate-tasks` to create a task list from the PRD.
  * Use `/process-task-list` to manage and track task progress.

Project structure looks like this:


    tree -a
    # .
    # ├── .claude
    # │   ├── commands
    # │   │   ├── create-prd.md
    # │   │   ├── generate-tasks.md
    # │   │   └── process-task-list.md
    # │   └── settings.local.json
    # ├── .mcp.json
    # └── README.md


For more details, please refer to [source code](https://github.com/NikiforovAll/claude-code-rules).

### Knowledge Mining / Grounding

### Miscellaneous

  * Use in “pipe” mode, as Unix philosophy utils: `claude -p ""` or `echo '' | claude -p ""`.
  * 🗑️ `/clear` and `/compact <specific prompt for aggregation>` can be very helpful.
  * 🧠 If you don’t know something about Claude Code, ask it\! It’s self-aware.
    * E.g., What kind of tools do you have? Can you perform a web search?

## MCP Servers

You can use MCP servers. See [claude-code/mcps](https://docs.anthropic.com/en/docs/claude-code/mcps).

Here is an example of how to setup MCP servers, just create a `.mcp.json` file in your project root:


    {
      "mcpServers": {
        "microsoft.docs.mcp": {
          "type": "http",
          "url": "https://learn.microsoft.com/api/mcp"
        },
        "context7": {
          "type": "stdio",
          "command": "npx",
          "args": [
            "-y",
            "@upstash/context7-mcp@latest"
          ]
        }
      }
    }


#### 🎁 Bonus: Turn Claude Code into an Interactive Tutor with Microsoft Docs & Context7

You can supercharge Claude Code by integrating it with Microsoft Docs and Context7. It can be useful for learning and development tasks.

## Useful Links

* * *

If you have questions or want to see more, check out the [GitHub repository](https://github.com/NikiforovAll/claude-code-rules) or leave a comment below\!