---
author: Adriana Villela
domain: dt-url.net
extraction_timestamp: '2025-06-13T23:07:43.542128Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:43.542155Z'
found_in_posts:
- at://did:plc:jkloammkxhs5qef3oiaxluog/app.bsky.feed.post/3lrg4ywh76223
language: en
medium: Medium
stage: fetched
title: Querying OpenTelemetry Data with the Dynatrace MCP Server | by Adriana Villela
  | Women in Technology | Jun, 2025 | Medium
url: https://dt-url.net/dt-mcp-medium
word_count: 2698
---

# Querying OpenTelemetry Data with the Dynatrace MCP Server | by Adriana Villela | Women in Technology | Jun, 2025 | Medium

# Querying OpenTelemetry Data with the Dynatrace MCP Server

## A Natural Language Approach

Sunlight peeking through leaves in late afternoon. Photo by [Adriana Villela](https://instagram.com/adrianamvillela).

Ever since I learned about [MCP servers](/womenintechnology/lets-learn-about-mcp-together-be1601dc7a81), I couldn’t wait to get some hands-on experience with them. My interest in MCP servers, however, is less about trying to build my own. I mean, that’s cool and all, but I really want to leverage existing MCP servers for Observability-related workflows. I thought I’d start out small and try my hand at using natural language to query [OpenTelemetry \(OTel\)](https://opentelemetry.io) data. And it so happens that [Dynatrace has an MCP server](https://dt-url.net/mcp) that allows me to do just that.

So today I’ll walk you through configuring the Dynatrace MCP server to interact with OpenTelemetry data ingested into Dynatrace via the [OpenTelemetry Demo App](https://github.com/open-telemetry/opentelemetry-demo).

Let’s do this\!

> 🌈 **NOTE:** Although this tutorial is geared towards the Dynatrace MCP server, there are a number of useful little nuggets that apply to configuring MCP servers in VSCode for use with GitHub Copilot\!

# Tutorial

Having experience with Dynatrace will help you get the most out of this tutorial, so if you need a bit of a refresher check out my video series, [Dynatrace Can Do THAT with OpenTelemetry?](https://dt-url.net/dt-loves-otel-yt)

## Enable MCP Support in VSCode

This tutorial uses VSCode’s [built-in GitHub Copilot chat support](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_enable-mcp-support-in-vs-code). Copilot supports multiple large language models \(LLMs\), including GPT-4 and Claude, and you can select which one you wish to use. The underlying LLM used by Copilot chat is your MCP client, and it communicates with Dynatrace via the Dynatrace MCP server.

But, before you can use GitHub Copilot chat, you’ll need to [enable MCP support in VSCode](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_enable-mcp-support-in-vs-code). You can do this by adding `“chat.mcp.enabled”: true` to your `settings.json` file. And where is `settings.json`, you ask? If you’re like me and always have to look it up, I’ve got you:

  * [Development \(dev\) container](https://containers.dev/) \(if you’re using one\) scope: `/home/vscode/.vscode-server/data/Machine/settings.json`
  * User scope on the Mac: `$HOME/Library/Application Support/Code/User/settings.json`
  * For other systems: check out the [VSCode docs](https://code.visualstudio.com/docs/getstarted/settings#_settings-json-file)

> ✨ **NOTE:** Copilot chat support is an experimental feature in VSCode.

## Send OTel data to Dynatrace

Since our ultimate goal is to query OTel data in Dynatrace, we first need to ensure that we _have_ OTel data in Dynatrace. If you already have an app that’s sending OTel data to Dynatrace, then awesome. You can skip on to the next section.

If you don’t have OTel data in Dynatrace yet, don’t worry — I’ve got you. The easiest way to do this is to configure and run the [OpenTelemetry Demo App](https://github.com/open-telemetry/opentelemetry-demo) to send OTel data to Dynatrace. You can check out [my tutorial](https://dt-url.net/otel-demo-medium) for guidance on how to do that.

Once the Demo App has started sending data to Dynatrace, you can move on to the next step.

## Dynatrace MCP Server Configuration

Now for the fun stuff\! As I mentioned earlier, the LLM used by Copilot chat talks to Dynatrace via the Dynatrace MCP server. In order for that to happen, we must make Copilot aware of the Dynatrace MCP server. How do we do that? Let me walk you through.

**1- Create MCP server configuration file**

To add an MCP server to your workspace, you’ll first need to create a file called `mcp.json`:


    mkdir .vscode
    touch .vscode/mcp.json

This file contains a list of MCP servers that you would like Copilot to use.

**2- Add the Dynatrace MCP server**

Now we can add the [Dynatrace MCP server](https://dt-url.net/mcp) to `mcp.json`:


    tee -a .vscode/mcp.json <<EOF
    {
      "servers": {
        "npx-dynatrace-mcp-server": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"],
          "envFile": "${workspaceFolder}/.env"
        }
    }
    EOF

Great. So what do these configurations options mean? Let’s dig in:

  * `servers`: Root configuration element. All MCP servers go under here.
  * `npx-dynatrace-mcp-server`: the name of the MCP server that we’re configuring. This name can be anything you want, even `Dynatrace MCP server`, spaces and all. I just went with the configuration given in [Dynatrace MCP server readme](https://github.com/dynatrace-oss/dynatrace-mcp?tab=readme-ov-file#quickstart).
  * `type`: The connection type. Valid values are: `stdio`, `sse`, and `http`. In our case, we’re using `stdio`, which means that a copy of the Dynatrace MCP server runs locally in VSCode. `sse` and `http` are used for accessing remote MCP servers. For more information on remote vs. local MCP servers, check out [this great overview](https://www.apideck.com/blog/understanding-local-and-remote-model-context-protocols).
  * `command`: The command to run the MCP server. Since our `type` is `stdio`, the Dynatrace MCP server will run locally, so we need a command to run the server. The Dynatrace MCP server is available as an executable [npm package](https://docs.npmjs.com/about-npm), so it uses the `[npx](https://docs.npmjs.com/cli/v8/commands/npx)` command to run it.
  * `args`: The arguments passed to the `npx` command. Here, we have 2 args. the `-y` arg tells `npx` to install dependent packages without prompting, and the second arg includes the package name \(`dynatrace-oss/dynatrace-mcp-server`\), and version \(`latest`\).
  * `envFile`: Environment variable file. In our case, includes environment variables required to authenticate and connect to Dynatrace. This configuration says that it is looking for a `.env` file located in the VSCode workspace root.

**3- Configure the**`**.env**`**file**

Before we can start up the Dynatrace MCP server, we need to [create an OAuth Client](https://github.com/dynatrace-oss/dynatrace-mcp?tab=readme-ov-file#environment-variables) so that the MCP server to talk to Dynatrace. For this, we will need to add the following environment variables to `.env`:


    OAUTH_CLIENT_ID="<your_dt_oauth_client_id>"
    OAUTH_CLIENT_SECRET="<your_dt_oauth_secret>"
    DT_ENVIRONMENT="https://<your_dt_tenant>.apps.dynatrace.com"
    DT_API_TOKEN="<your_dt_api_token>"

To create your Dynatrace OAuth Client, follow the instructions [here](https://docs.dynatrace.com/docs/manage/identity-access-management/access-tokens-and-oauth-clients/oauth-clients).

To generate a `DT_API_TOKEN`, check out [my blog post on sending OTel data to Dynatrace](/womenintechnology/how-do-i-send-opentelemetry-data-to-dynatrace-842cebb21286).

**4- Start the Dynatrace MCP server**

You are now ready to start the Dynatrace MCP server\! To start the MCP server, open up `mcp.json` in VSCode. Just above the server name, in our case, `npx-dynatrace-mcp-server`, you should see the word “Start”. Click on that to start the MCP server.

Start the MCP server by clicking on the word Start just above the server name

Once the MCP server is started, you should see “Running” in place of “Start”:

The MCP server is now running.

FYI — If your MCP server craps out on startup, you’ll know. Your Output tab in VSCode will be sure to tell you, just like it told me.

Uh-oh\! Error on MCP server startup.

In my case, this error was caused by an incorrect URL in `DT_ENVIRONMENT`.

**5- Start up the chatbot**

Great. Now what? Now Copilot is ready to talk to Dynatrace\! Uh, but where’s the chat window?

Click on the little chat icon just to the right of the [command palette](https://code.visualstudio.com/api/ux-guidelines/command-palette) in VSCode, and select “Open Chat”.

Open chat options

This will open up a chat window. You will also be prompted to enable GitHub Copilot.

> **✨ NOTE:** [GitHub copilot has a free tier](https://github.com/features/copilot/plans), which limits you 50 agent mode or chat requests per month.

Once chat is enabled, make sure that you have your chat on Agent mode.

To switch to Agent mode, navigate to the bottom right-hand side of the chat input box.

Switch between Ask, Edit, and Agent modes

So what’s the difference between Ask and Agent modes? Ask mode is used for lookups and research type tasks. Agent mode allows copilot to do things on your behalf, like modify code and configuraitons, dependin on what MCP servers it’s interacting with.

Learn more about the differences between Ask, Edit, and Agent mode [here](https://github.blog/ai-and-ml/github-copilot/copilot-ask-edit-and-agent-modes-what-they-do-and-when-to-use-them/).

## Talk to Dynatrace\!

Now that everything is started up, you might be wondering, “What can I actually DO with this thing?” Great question. Here are some example prompts that I used. Note that some of your results may vary.

**Prompt 1: How many unique services are running in Dynatrace?**

**Result:**


     1. checkout
    2. flagd
    3. frontend
    4. recommendation
    5. frontend-web
    6. product-catalog
    7. ad
    8. currency
    9. frontend-proxy
    10. cart
    11. image-provider
    12. load-generator

List of unique services running in Dynatrace

**Prompt 2: List all of the logs under the most recent trace\_id**

**Result:**


     Here are all the logs under the most recent trace_id (da21adc12e78ec179a4a97c6c85e27cf):
    1. [2025-06-11T15:52:44.229Z]
    Message: Receive ListRecommendations for product ids: ['LECAV7KIM', 'OPUK6V6EVO, '2ZYFJ3GM2N', 'HQTGWGPNH4',
    'OLJCESPC7Z']
    Service: recommendation

    2. [2025-06-1115:52:44. 2222]
    Message: [2025-06-11T15:52:44.222Z] "GET /api/recommendations?productlds=&sessionld=7f704470-8da0-4052-ab22-a69f0ca0391f&CurrencyCode=CHF HTTP/1.1" 200 - via_upstream - ...
    Service: frontend-proxy

    3. [2025-06-11T15:52:52.999Z]
    Message: Convert conversion successful
    Service: currency

    4. [2025-06-11T15:52:52.999Z]
    Message: Convert conversion successful
    Service: currency

    5. [2025-06-11T15:52:52.999Z]
    Message: Convert conversion successful
    Service: currency

    6. [2025-06-11T15:52:52.999Z]
    Message: Convert conversion successful
    Service: currency

Listing of all logs under the most recent trace\_id

**Prompt 3: What’s the average response time for the currency service?**

**Result:**


     The average response time for the "currency" service is approximately 4,639 milliseconds (about 4.6 seconds).

Average response time for the currency service

**Prompt 4: What does this DQL query do:**`**timeseries { sum(app_recommendations_counter), value.A = avg(app_recommendations_counter, scalar: true) }**`

**Result:**


     This DQL query:

    timeseries { sum(app_recommendations_counter), value.A = avg(app_recommendations_counter, scalar: true) }

    does the following:

    * Plots a timeseries for the metric app_recommendations_counter.
    * For each time interval, it calculates and displays the sum of app_recommendations_counter values (i.e., the total count in that interval).
    * It also calculates value.A, which is the overall average (scalar: true means it's a single value for the whole series, not per interval) of app_recommendations_counter across the entire timespan.
    * The result is a chart or table showing the sum at each interval and a constant line or value for the overall average.

    This is useful for comparing interval totals to the overall average for the metric.

Breakdown of the DQL timeseries query for app\_recommendations\_counter

## Gotchas

OF COURSE, nothing works perfectly the first time \(I WISH\!\), and I did encounter a few gotchas along the way:

**1- Executables**

Since the Dynatrace MCP server runs locally using `npx`, it means that you need to [install NodeJS on your machine](https://nodejs.org/en/download), and then install `npx` using `npm install -g npx`.

Other MCP servers may also run using `npx`. But they also might not. For example:

Bottom line, look at the command used by your MCP server to make sure that you have the correct executables installed on your machine.

> ✨ **NOTE:** To save you some pain, feel free to use my [MCP Playground GitHub repo](https://dt-url.net/av-mcp-playground), which has everything you need, in a dev container. Because I love dev containers. _😁_

**2- Missing Dynatrace API token**

The first time I ran the Dynatrace MCP server, everything was humming along nicely, until I got this error message the next day:


    Your Dynatrace MCP authentication token has expired, so I cannot retrieve the
    list of services at this time. Please refresh your credentials in the
    .env file and restart the MCP server. Once re-authenticated, I can fetch and
    display the list of services for you.

    Let me know when you've updated your credentials!

Um…what? So I asked the chatbot to elaborate, and it told me:


    To renew your Dynatrace MCP authentication token:

    1. Get a new Dynatrace API token:
    • Log in to your Dynatrace web Ul.
    • Go to Settings → Integration → Dynatrace API.
    • Create a new API token with the required permissions (or use an existing valid one).

    2. Update your s .env.av file in your workspace:
    • Open .env (the file referenced by envFile in your MCP config).
    • Find the line with your old Dynatrace token (e.g., DT_API_TOKEN=... or similar).
    • Replace the old token value with your new token.
    • Save the file.

    3. Restart the MCP server in VS Code:
    • Stop the running Dynatrace MCP server if it's running.
    • Start it again so it loads the new token.

Luckily, I already had a `DT_API_TOKEN` kicking around from sending data from the OpenTelemetry Demo to Dynatrace, so I added my `DT_API_TOKEN` to my `.env` file, so the final file looked something like this:


    OAUTH_CLIENT_ID="<your_dt_oauth_client_id>"
    OAUTH_CLIENT_SECRET="<your_dt_oauth_secret>"
    DT_ENVIRONMENT="https://<your_dt_tenant>.apps.dynatrace.com"
    DT_API_TOKEN="<your_dt_api_token>"

If you need a refresher on how to generate a `DT_API_TOKEN`, check out [my blog post on sending OTel data to Dynatrace](/womenintechnology/how-do-i-send-opentelemetry-data-to-dynatrace-842cebb21286).

> ✨ **NOTE:** I’ve [logged a bug in the Dynatrace MCP GitHub repo](https://github.com/dynatrace-oss/dynatrace-mcp/issues/27), to ensure that the README is updated to include the `DT_API_TOKEN`.

**3- Querying issues**

I was trying to do some natural-language querying to find all spans with a given trace ID that I KNEW existed in Dynatrace.

**My prompt:** give me all spans with give me all spans with a traceid 40f771df568dc260507b501872785cb8

**Result:** There are no spans with traceID 40f771df568dc260507b501872785cb8

Wut? What was up, y’all?

Unable to find a trace with the given trace ID that DEFINITELY existed

Well, fortunately, the chat responses include the [Dynatrace Query Language \(DQL\)](https://docs.dynatrace.com/docs/discover-dynatrace/references/dynatrace-query-language) queries that are generated from my natural-language prompt, so I could see what was going on. And what was the issue, you might ask?

Well, it was sending the following DQL query to Dynatrace:


    fetch spans
    | filter traceId == "40f771df568dc260507b501872785cb8"

The problem is that it was searching on `traceId`, and not `trace_id`. Once I told Copilot to search on `trace_id`, the problem was resolved.

**Revised prompt:** fetch logs with field trace\_id “40f771df568dc260507b501872785cb8”

> ✨ **NOTE:** I’ve [logged a bug in the Dynatrace MCP GitHub repo](https://github.com/dynatrace-oss/dynatrace-mcp/issues/26), so hopefully this gets resolved soon, but at least there’s a workaround\!

# Final Thoughts

I have to admit that being able to interact with OpenTelemetry data in Dynatrace using natural language was mind-blowingly cool. I’m still pretty new to DQL and I find myself looking things up all the time, so this definitely makes things a lot easier for me. Plus, since the Copilot spits out the DQL query that it sends to Dynatrace, I use it as a way to up my DQL skills.

The Dynatrace MCP server is still relatively new, so of course there are still some hiccups to work out, but damn…colour me impressed by what I’ve seen so far. I’m super excited by what the future holds, and I can’t wait to see it evolve over time\!

And now, please enjoy this photo of Barbie \(top\) and Katie \(bottom\), cuddled up in their red house.

Barbie \(top\) and Katie \(bottom\) enjoying some cuddle time. Photo by [Adriana Villela](https://instagram.com/addrianamvillela).

Until next time, peace, love, and code. 🖖💜👩‍💻