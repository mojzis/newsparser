---
author: null
domain: nicolaiarocci.com
evaluation:
  evaluated_at: '2025-06-13T23:10:48.836217Z'
  evaluator: claude-3-haiku-20240307
  is_mcp_related: true
  key_topics:
  - MCP
  - AI tool integration
  - Language models
  - MCP servers
  - LLM integration
  perex: Connecting apps to LLMs? This author's got the MCP protocol down to a science
    - a must-read for any AI enthusiast!
  relevance_score: 0.8
  summary: The article discusses the author's presentation on MCP, a protocol for
    integrating AI tools and language models, and their experiments with MCP servers
    and linking them to LLMs.
extraction_timestamp: '2025-06-13T23:07:36.343874Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:36.343984Z'
found_in_posts:
- at://did:plc:hxrfxsb3ksghe7z4i2pmh4qz/app.bsky.feed.post/3lrfgodiwac2i
language: en
medium: Nicola Iarocci
stage: evaluated
title: MCP or connecting our apps to LLMs | Nicola Iarocci
url: https://nicolaiarocci.com/mcp-or-connecting-our-apps-to-llms/
word_count: 253
---

# MCP or connecting our apps to LLMs | Nicola Iarocci

Last night, I presented a session titled [MCP or Connecting our Apps to LLMs](https://www.meetup.com/devromagna/events/308179204/) at DevRomagna, our local developer’s community, and I think it went well.

I had intended to record the audio with the idea of transcribing it with MacWhisper and then publishing it here on my site, but I forgot to do so, which is a pity.

The session lasted almost two hours \(I had thought it would take less time\), during which I deviated somewhat from the script, using slides as a guide that were essentially an adaptation of the notes I had taken during my experiments. I showed the code for the MCP servers I created \(stdio and streamable HTTP transports\), demonstrated the various ways to link them with LLMs \(Claude Desktop, Claude Code, and VS Code\), and then shared my thoughts on the entire matter.

I received quite a bit of feedback, both in the room and afterward, when we moved to a pub where we stayed quite late by my standards, discussing AI, LLMs, and their impact on our daily work, which we can certainly define as significant, if not massive. Everyone uses LLMs’ UIs at their job to some extent, but very few are currently into agentic coding \(the idea of a future session on that topic is tempting\).

One remarkable tool that surfaced during the pub chat is [Kotaemon](https://github.com/Cinnamon/kotaemon), _“an open-source RAG-based tool for chatting with your documents.”_.