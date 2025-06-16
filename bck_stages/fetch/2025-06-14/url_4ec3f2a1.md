---
author: Den Delimarsky
domain: isaacl.dev
extraction_timestamp: '2025-06-13T23:07:06.823056Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:06.823147Z'
found_in_posts:
- at://did:plc:yyhj5wloszrpj2wg5adb3ijs/app.bsky.feed.post/3lr6gonjy4422
language: en
medium: null
stage: fetched
title: Visual Studio Code Now Supports MCP Authorization · Den Delimarsky
url: https://isaacl.dev/gll
word_count: 505
---

# Visual Studio Code Now Supports MCP Authorization · Den Delimarsky

You what I am pumped about this week? The fact that the latest builds of Visual Studio Code now support the [new MCP authorization specification](https://modelcontextprotocol.io/specification/draft/basic/authorization). But not only that - if your MCP servers _do not_ support the new spec just yet, it does the right thing and falls back to the [`2025-03-26`](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization) version of the protocol.

Check this out - working with the [Sentry MCP server](https://docs.sentry.io/product/sentry-mcp/):

[ ](https://assets.den.dev/images/postmedia/vscode-authorization-mcp/sentry-authorization.gif) Sentry MCP authorization flow as seen in Visual Studio Code Insiders.

Sentry is still using the legacy implementation that has a shared client ID server-side and then does Dynamic Client Registration \(DCR\) prior to completing the flow. They are also using the neat little Confused Deputy prevention trick I just [blogged about yesterday](/blog/mcp-confused-deputy-api-management/).

This is cool and all, but you know what’s cooler? Bypassing the DCR requirement altogether if you are using Entra ID for your applications. Because Visual Studio Code already has a client registration with Entra ID, it doesn’t need to do anything special for MCP servers that support the new authorization spec and the [Protected Resource Metadata \(PRM\) document](https://datatracker.ietf.org/doc/rfc9728/). Check this magic out with a test MCP server that I am building as part of [introducing authorization spec support](https://github.com/modelcontextprotocol/csharp-sdk/pull/377) in the [MCP C\# SDK](https://github.com/modelcontextprotocol/csharp-sdk):

[ ](https://assets.den.dev/images/postmedia/vscode-authorization-mcp/vscode-new-spec-auth.gif) Authorization with Entra ID against a protected MCP server in Visual Studio Code Insiders.

Because Visual Studio Code integrates natively with the [Web Account Manager \(WAM\)](/blog/using-brokers-authentication-msal/), also known as the authentication broker, the user doesn’t even need to go through the browser flow - it’s all handled at the OS level. Visual Studio Code detects that Entra ID is declared in the PRM document \(discovered through a `HTTP 401` response\) and then uses its own client registration to kick off the flow. Smooth like butter on toast. I love me a developer experience that _gets out of the way and just works_.

And just like that, you can now access protected MCP servers in Visual Studio Code - both the ones that use the current stable spec, as well as the [brand-new PRM-based one](/blog/new-mcp-authorization-spec/).

Special kudos to [Tyler Leonhardt](https://github.com/TylerLeonhardt) for working _extremely hard_ in getting this implemented. MCP in Visual Studio Code wouldn’t be the same without his work.

To get started with protected MCP servers in Visual Studio Code, [download the latest version of Visual Studio Code Insiders](https://code.visualstudio.com/insiders/). And of course, if you run into issues or have questions, [let us know on GitHub](https://github.com/microsoft/vscode/issues)\!