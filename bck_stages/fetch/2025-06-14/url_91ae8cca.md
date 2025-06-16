---
author: null
domain: bit.ly
extraction_timestamp: '2025-06-13T23:07:29.767778Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:29.767805Z'
found_in_posts:
- at://did:plc:ruawxewohfdbtxzfd6mljk4w/app.bsky.feed.post/3lrdkuvcuek2d
language: en
medium: null
stage: fetched
title: 'Beyond Tool Calling: Understanding MCP''s Three Core Interaction Types - Upsun
  Developer Center'
url: https://bit.ly/3SOlXD5
word_count: 1243
---

# Beyond Tool Calling: Understanding MCP's Three Core Interaction Types - Upsun Developer Center

The Model Context Protocol \(MCP\) changes how AI applications connect to external data and services. While most developers have experience with tool calling, MCP offers three distinct interaction types that work together to create richer experiences: **prompts** , **resources** , and **tools**. Understanding these three primitives and when to use each one gives you more control over building AI-powered applications.

## The MCP interaction model

These three interaction types work together through what’s known as the “MCP interaction model”:

  * **Prompts** are user-driven, typically exposed through slash commands or menu options
  * **Resources** are application-driven, where the client decides how to use the data
  * **Tools** are model-driven, where the AI chooses when and how to call them

This gives you coverage across all three major actors in an AI application: the user, the application, and the model itself.


    graph TB
        User[👤 User] --> Prompts[📝 Prompts
    User-driven]
        App[🖥️ Application] --> Resources[📁 Resources
    Application-driven]
        Model[🤖 AI Model] --> Tools[🔧 Tools
    Model-driven]

        Prompts --> MCP[MCP Server]
        Resources --> MCP
        Tools --> MCP

        MCP --> ExternalSystems[External Systems
    APIs, Databases, Services]

        style Prompts fill:#D0F302,color:#000
        style Resources fill:#6046FF,color:#fff
        style Tools fill:#D0F302,color:#000
        style MCP fill:#000,color:#fff
        style ExternalSystems fill:#fff,color:#000

## Prompts: User-driven templates for AI interactions

Prompts in MCP are predefined templates that users can invoke directly. Think of them as shortcuts or examples that help users get started with your MCP server’s capabilities.

### Why prompts matter

As the creator of an MCP server, you know best how your tools should be used. Prompts let you provide users with working examples they can invoke immediately, rather than expecting them to figure out the right way to phrase their requests.

### How prompts work

The prompt interaction follows a specific flow between the user, client application, and MCP server:


    sequenceDiagram
        participant User
        participant Client
        participant MCP as MCP Server
        participant API as External API

        User->>Client: Invoke prompt "analyze-project"
        Client->>MCP: prompts/get request
        MCP->>API: Fetch live data (logs, code)
        API-->>MCP: Return current data
        MCP->>MCP: Generate dynamic prompt with context
        MCP-->>Client: Return formatted prompt messages
        Client->>Client: Add to AI context
        Client->>User: Display AI response

### Dynamic prompt capabilities

Under the hood, prompts are just code, which means they can be dynamic. They can:

  * Fetch live data from APIs
  * Include current system state
  * Offer autocomplete for arguments
  * Adapt based on user context

Here’s how you might implement a dynamic prompt in TypeScript:

### When to use prompts

Use prompts when you want to:

  * Provide examples of how to use your MCP server
  * Give users shortcuts for common workflows
  * Include dynamic context that would be tedious to type manually
  * Onboard new users with working examples

## Resources: Application-driven data exposure

Resources represent raw data that your MCP server can expose to client applications. Unlike prompts that users invoke or tools that models call, resources are consumed by the application itself.

### The power of application choice

Resources give applications complete freedom in how they use your data. A client might:

  * Build embeddings for retrieval-augmented generation \(RAG\)
  * Cache frequently accessed data
  * Transform data for specific use cases
  * Combine multiple resources in novel ways



    graph LR
        MCP[MCP Server] --> |exposes| Resources[📁 Resources]
        Resources --> App1[🔍 RAG System
    Build embeddings]
        Resources --> App2[💾 Cache Layer
    Store frequently used data]
        Resources --> App3[📊 Analytics
    Transform & analyze]
        Resources --> App4[🔄 Integration
    Combine multiple sources]

        style MCP fill:#000,color:#fff
        style Resources fill:#6046FF,color:#fff
        style App1 fill:#D0F302,color:#000
        style App2 fill:#D0F302,color:#000
        style App3 fill:#D0F302,color:#000
        style App4 fill:#D0F302,color:#000

### Resource types

MCP supports two types of resources:

**Direct resources** have fixed URIs and represent specific data:

**Resource templates** use URI templates for dynamic resources:

### Implementing resources

Here’s a Python example showing how to expose database schemas as resources:

### When to use resources

Use resources when you want to:

  * Expose raw data for the application to process
  * Enable RAG implementations
  * Provide data that applications might cache or index
  * Support multiple data consumption patterns

## Tools: Model-driven actions

Tools are the most familiar MCP primitive—functions that the AI model can choose to call during conversations. They represent actions your MCP server can perform.

### Tool design principles

Effective tools should:

  * Have clear, descriptive names
  * Include comprehensive descriptions
  * Define precise input schemas
  * Return structured, helpful results

### Tool implementation

Here’s a TypeScript example of a calculation tool:

### How tools work in practice

Tools follow the familiar function calling pattern, but within the MCP framework:


    sequenceDiagram
        participant User
        participant Client
        participant Model as AI Model
        participant MCP as MCP Server
        participant System as External System

        User->>Client: "Calculate the sum of 5 and 3"
        Client->>Model: Send message with available tools
        Model->>Model: Decide to use calculate_sum tool
        Model->>Client: Tool call request
        Client->>MCP: tools/call calculate_sum
        MCP->>System: Perform calculation
        System-->>MCP: Return result
        MCP-->>Client: Tool result
        Client->>Model: Provide tool result
        Model->>Client: Generate response with result
        Client->>User: "The sum is 8"

### When to use tools

Use tools when you want the AI to:

  * Perform actions on behalf of users
  * Query external systems
  * Transform or process data
  * Make decisions about when to invoke functionality

## Bringing it all together: A GitHub issue tracker example

Here’s how these three primitives work together in a GitHub issue tracker MCP server:


    flowchart TD
        User[👤 Developer]
        App[🖥️ AI Application]
        Model[🤖 AI Model]

        User --> Prompts[📝 Prompts
    Summarize recent issues
    Review PR feedback]
        App --> Resources[📁 Resources
    Repository metadata
    Issue lists & histories
    Pull request data]
        Model --> Tools[🔧 Tools
    Create issue
    Update labels
    Assign team members
    Search repositories]

        Prompts --> MCP[GitHub MCP Server]
        Resources --> MCP
        Tools --> MCP

        MCP --> GitHub[🐙 GitHub API]

        style Prompts fill:#D0F302,color:#000
        style Resources fill:#6046FF,color:#fff
        style Tools fill:#D0F302,color:#000
        style MCP fill:#000,color:#fff
        style GitHub fill:#fff,color:#000

**Prompts** provide shortcuts like “summarize recent issues” with autocomplete for project repositories and milestones, giving users an easy way to catch up on project status and outstanding work.

**Resources** expose repository metadata, issue lists, pull request data, and commit histories that applications can use for embeddings, caching, or building comprehensive project dashboards.

**Tools** handle actions like creating issues, updating labels, assigning team members, and searching across repositories that the AI can invoke as needed based on user requests.

This combination allows users to interact with GitHub repositories through natural language while giving applications the flexibility to process GitHub data in sophisticated ways.

By using all three interaction types together, you create a much richer experience than tool calling alone could provide.

## Building richer MCP experiences with Upsun

When you’re building MCP servers that take advantage of these three interaction types, you need a platform that can handle the complexity. Upsun’s Cloud Application Platform provides the infrastructure you need:

  * **Preview environments** let you test MCP server changes in production-like environments
  * **Multi-app architecture** supports complex MCP implementations with multiple services
  * **Built-in observability** helps you monitor MCP server performance and usage
  * **Git-driven infrastructure** ensures your MCP server deployments are consistent and version-controlled

The combination of prompts, resources, and tools gives you powerful building blocks for AI applications. With Upsun handling the infrastructure complexity, you can focus on creating innovative MCP servers that provide real value to users.

Ready to build your own MCP server? [Start with a free Upsun account](https://upsun.com/) and explore how these interaction types can transform your AI applications.