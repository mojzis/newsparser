---
author: null
domain: community.openai.com
evaluation:
  evaluated_at: '2025-06-14T21:55:31.493365Z'
  evaluator: claude-3-haiku-20240307
  is_mcp_related: true
  key_topics:
  - MCP
  - Zero Trust Architecture
  - Pomerium
  - OAuth
  - AI tool integration
  perex: Securing MCP servers the zero-trust way - no more exposed tokens or risky
    OAuth flows.
  relevance_score: 0.9
  summary: Building secure, zero-trust MCP servers to access OAuth-based services
    like GitHub and Notion. Pomerium proxy handles authentication and token management,
    enabling safe MCP integrations.
extraction_timestamp: '2025-06-14T21:55:24.171129Z'
fetch_status: success
fetched_at: '2025-06-14T21:55:24.171171Z'
found_in_posts:
- at://did:plc:vug3vkycxfjbkiwsyyrak4gh/app.bsky.feed.post/3lrl5hugy622y
language: en
medium: OpenAI Developer Community
stage: evaluated
title: Zero Trust Architecture for MCP Servers Using Pomerium - Community - OpenAI
  Developer Community
url: https://community.openai.com/t/zero-trust-architecture-for-mcp-servers-using-pomerium/1288157
word_count: 452
---

# Zero Trust Architecture for MCP Servers Using Pomerium - Community - OpenAI Developer Community

We’ve been building some open-source tools to make it easier to run remote MCP servers securely using Zero Trust principles — especially when those servers need to access upstream OAuth-based services like GitHub or Notion.

**Pomerium** acts as an identity-aware proxy to:

  * Terminate TLS and enforce Zero Trust at the edge
  * Handle the full OAuth 2.1 flow for your MCP server
  * Keep upstream tokens \(e.g., GitHub, Notion\) out of reach from clients

Our **demo app** \(_MCP App Demo_\) uses the OpenAI Responses API to show how LLM clients \(like ChatGPT’s Connectors\) can securely call MCP servers — without embedding tokens or managing OAuth themselves.

The companion project, _MCP Servers_ , includes reference implementations \(e.g., Notion\) already integrated with Pomerium. You can find both on GitHub under `pomerium/mcp-app-demo` and `pomerium/mcp-servers`.

I can’t post links yet \(still new here\), but happy to share more details or walk you through the setup if you’re curious.

1 Like

Looks like someone already shared them as a comment. Thanks [@EricGT](/u/ericgt) and [@aprendendo.next](/u/aprendendo.next)\!

3 Likes

I was lucky enough to be able to attend the first ever MCP Dev Summit, and there were so many great talks. There wasn’t enough room in the one day for all the talks, so they moved some to online meetups where I gave a talk about these projects, “Agentic Access: OAuth Isn’t Enough | Zero Trust for AI Agents w/ Nick Taylor \(Pomerium + MCP\)”. See youtube dot com/watch?v=KY1kCZkqUh0

1 Like

I’m still highly skeptical of the mcp approach, but zero trust as a security standard is great

if mcp turns out to be the way, great, if not…

has anything changed in the 2 months since this was posted by fireship?

1 Like

Totally fair to be skeptical. It’s still unclear if this is the long-term direction but it’s been cool to see the ecosystem evolve so quickly since this only came out last November.

But what I saw in the Fireship video is _exactly_ why we’re doing what we’re doing. It’s a super cool demo, but the server is wired directly to prod data with no auth, no rate limits, and zero guardrails. Security feels like an afterthought — or maybe just not considered at all.

Even with OAuth support in the MCP spec now, that’s not enough. I mentioned in a comment above that OAuth alone doesn’t solve dynamic authorization or token exposure. If this pattern keeps gaining traction, we need stronger defaults that handle identity and policy enforcement _before_ tools get called.

Like Spiderman’s Uncle Ben always said…