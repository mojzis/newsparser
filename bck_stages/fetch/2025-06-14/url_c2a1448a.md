---
author: '@apollographql'
domain: apollographql.pulse.ly
extraction_timestamp: '2025-06-13T23:06:57.214573Z'
fetch_status: success
fetched_at: '2025-06-13T23:06:57.214597Z'
found_in_posts:
- at://did:plc:wiwzl74lo4ikpgcmawy4oa5c/app.bsky.feed.post/3lrb5yannew2e
language: en
medium: null
stage: fetched
title: 'Building MCP Tools with GraphQL: A Better Way to Connect LLMs to Your API
  | Apollo GraphQL Blog'
url: https://apollographql.pulse.ly/asmicjvth3
word_count: 1101
---

# Building MCP Tools with GraphQL: A Better Way to Connect LLMs to Your API | Apollo GraphQL Blog

After Apollo recently released the Apollo MCP Server that allows you to generate tools for any GraphQL API, I have been investigating MCP server development within Python and Typescript frameworks. It’s easy enough to build a simple tool, but I found myself feeling déjà vu as if I were building applications before GraphQL was released. Each tool I wrote started to get more complex and I quickly started seeing multiple API fetches happen in the same tool.

For this blog post, we’re going to look more deeply at The Space Devs APIs and the community launch library MCP server that is built in Python with the Launch Library REST API. Then we’ll look at how GraphQL can simplify the development process and provide better tools for LLM interaction.

## [](/blog/building-mcp-tools-with-graphql-a-better-way-to-connect-llms-to-your-api#building-simple-tools-a-tool-for-every-rest-api-endpoint)Building simple tools: A tool for every REST API endpoint

One pattern I tried developing with is making a simple tool for every Entity defined in my endpoints. This would cover returning a list of those entities in a “simplified” format that returns a subset of fields along with a detailed entity tool that returns all the fields for the entity. This is a commonly recommended pattern and here is an example of that from the launch library MCP server:


    @mcp_llv2.tool() async def launches_list(...)
    @mcp_llv2.tool() async def launches_detailed(...)

Overall this pattern works, but using REST means that each tool is additional code that has to be written and deployed to the MCP server. Even if you have an auto-generated REST API client, there still can be a lot of hand written code. For example, the launches\_list tool contains code that is primarily related to transforming the shape of the data:


    items = []
    for x in result.results:
        items.append(
            {
                "id": x.id,
                "net": f"{x.net} presision: {x.net_precision.name}",
                "name": x.name,
                "slug": x.slug,
                "status": x.status.abbrev,
                "rocket": x.rocket.configuration.full_name,
                "orbit": x.mission.orbit.abbrev,
                "provider": x.launch_service_provider.name,
                "location": x.pad.location.name,
                "launch_designator": x.launch_designator,
                "window": (
                    f"{x.window_start} -{x.window_end}"
                    if x.window_start and x.window_end
                    else None
                ),
            }
        )
    return yaml.dump(
        {
            "count": result.count,
            "next": result.next,
            "previous": result.previous,
            "launches": items,
        },
        allow_unicode=True,
        sort_keys=False,
    )

Each new API endpoint brings in one or two additional tools and the pattern starts to have the LLM act as an API query planner based on these tools. There are two things to be cautious about with general REST API responses:

  1. **Context window bloat** – as the LLM uses more tools and orchestrates the responses, additional fields that aren’t relevant to the initial question can begin to add unnecessary noise to the context window.
  2. **API Orchestration Distractions for LLMs** – each tool should encapsulate everything you need to give the proper context to the LLM for that piece of functionality. Having an LLM run through two or more tools for a given functionality because the API is broken apart is going to create additional processing overhead that is going to potentially confuse LLMs and cost more as additional tool calls are required.

## [](/blog/building-mcp-tools-with-graphql-a-better-way-to-connect-llms-to-your-api#graphql-operations-as-mcp-tools)GraphQL Operations as MCP Tools

GraphQL initially became popular with web developers in the promise of providing an operation as the contract of data needed for a given UI functionality. Agentic experiences will also have many of the functionalities our websites have and it makes sense to map a GraphQL operation to that functionality. Defining GraphQL operations as MCP tools means:

  * No writing tool code, just define the fields you need in the operation
  * The graph does the API orchestration, not the LLM
  * Adding or updating tools can be done without code deployments

To demonstrate a comparison, we created a GraphQL API for the Launch Library to create MCP tools with. In the Apollo MCP Server repository is an example operation that can be used to create an MCP tool for searching upcoming launches. GraphQL provides nice documentation capabilities that we can use to make tool descriptions. We default to comments and return type information defined in your schema but you can simply override that description by adding a comment to the top of your operation.

A nice benefit about this is how the LLM can use guided context to help re-execute the tools we defined. For example, we provide some information around the search term being best as codes or single words. The LLM understands this tool is best for short searches and can re-run them.

## [](/blog/building-mcp-tools-with-graphql-a-better-way-to-connect-llms-to-your-api#improved-developer-experience)Improved developer experience

Along with having no code for your MCP tools, writing those MCP tools is simple. GraphQL endpoints have options like [Apollo Explorer](https://thespacedevs-production.up.railway.app/) that give you a sandbox to author and test out operations that you could then run as tools. If you open the `/graphql/TheSpaceDevs` folder up in VS Code, you’ll see how you can have completion options for fields available in your schema as you write the operations:

## [](/blog/building-mcp-tools-with-graphql-a-better-way-to-connect-llms-to-your-api#mcp-tool-generative-capabilities)MCP Tool Generative Capabilities

You might also want to just have the LLM be a little more curious and learn about the schema to generate operations for tools or even to just dynamically execute. The `--introspection` option allows the LLM to enter the schema at any node and navigate the tree to keep the context window concise to the task at hand.

Here’s an example of the tool in action with Claude:

## [](/blog/building-mcp-tools-with-graphql-a-better-way-to-connect-llms-to-your-api#conclusion)Conclusion

When you need to write MCP tools for your APIs, GraphQL gives you a serious advantage in rapid iteration. A series of tools can be created in minutes and getting started is just a single command. You can [get started today](https://www.apollographql.com/docs/apollo-mcp-server/quickstart) with any GraphQL API, no API key or account required.

[Check out](https://www.apollographql.com/events/get-started-with-mcp-tools-for-your-graphql-api-today) my latest Apollo livestream from 5/21/2025 where I dive into developer workflows like hot-reloading with your MCP server with some Q&A at the end for MCP questions.