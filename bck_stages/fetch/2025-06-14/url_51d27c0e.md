---
author: Stijn Willems
domain: medium.com
extraction_timestamp: '2025-06-13T23:06:55.966634Z'
fetch_status: success
fetched_at: '2025-06-13T23:06:55.966659Z'
found_in_posts:
- at://did:plc:d52dvgrxurnliakcm6z3spq6/app.bsky.feed.post/3lriou5zrhk2k
language: en
medium: Medium
stage: fetched
title: 'Building the Ultimate Developer Timesheet: Correlating ActivityWatch, Voice
  Commands, and AI Analysis | by Stijn Willems | Jun, 2025 | Medium'
url: https://medium.com/@doozMen/building-the-ultimate-developer-timesheet-correlating-activitywatch-voice-commands-and-ai-ab0175a7a4d3
word_count: 449
---

# Building the Ultimate Developer Timesheet: Correlating ActivityWatch, Voice Commands, and AI Analysis | by Stijn Willems | Jun, 2025 | Medium

Ever wondered what your _actual_ productivity patterns look like? Not just “I worked 8 hours” but the granular reality of context switches, focus sessions, and the elusive billable vs. non-billable work distinction?

I just built a system that correlates multiple data sources to create the most comprehensive developer timesheet I’ve ever seen. Here’s how it works and what I learned.

# The Problem with Traditional Time Tracking

Most time tracking tools capture one dimension:

  * **Manual timers** : Rely on human memory \(we’re terrible at this\)
  * **App trackers** : Show what’s open, not what you’re actually doing
  * **Calendar blocks** : Show intent, not reality

But real work is messy. You’re coding in Xcode, jumping to Terminal for git commits, checking Slack for team updates, testing in Simulator, and maybe dictating notes via voice commands. Traditional tools miss this complexity.

# The Multi-Source Solution

I combined three data streams to get the full picture:

# 1\. ActivityWatch \(Window Tracking\)


    # Captures every app switch with timestamps
    09:05:22 - Xcode (CueApp — AppDelegate.swift) - 25m
    09:30:45 - Terminal (git commit -m "CA-5006 implementation") - 3m
    09:33:12 - Slack (Team coordination) - 8m

# 2\. Wispr Flow \(Voice Commands\)


    3:24 PM: "Let's add context that I stopped working for Medias now.
             I'm working on my side project."
    3:31 PM: "I'm working on a tool to work with Wispr Flow, which captures
             my notes that I send to Claude Code."

# 3\. MCP Server Integration

Using Model Context Protocol to feed all this data to Claude for intelligent analysis and correlation. And this is where the magic happened\! This is what I want to talk about more in upcoming blog posts. To me, it revealed something. It revealed the future that made me happy about coding again. Here I had the idea yesterday to ask Claude how to build MCP servers. I didn’t know how to yet. Together we built them. He found open source tools, we combined them, and I added in to Cloud Desktop. This resulted in this nice tool for myself that I for once didn’t spend too much time on, it actually works, and then I actually enjoy using. Let’s see what we can build next\!

# The Bigger Picture

We’re moving toward a world where our tools understand our work patterns better than we do. By combining multiple data sources — behavioral tracking, voice interaction, and AI analysis — we can build systems that not only track what we do but understand _why_ and _how_ we work.

The result? Better billing accuracy, improved focus patterns, and insights that actually help us work smarter. Most importantly, it’s a delight use and build conversational.