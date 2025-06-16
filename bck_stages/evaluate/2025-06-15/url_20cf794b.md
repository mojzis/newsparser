---
author: null
domain: awakari.com
evaluation:
  evaluated_at: '2025-06-15T22:04:40.554432Z'
  evaluator: claude-3-haiku-20240307
  is_mcp_related: false
  key_topics:
  - Awakari app
  - public/private interests
  - interest management
  perex: Awakari - a social app for sharing your interests, public or private.
  relevance_score: 0.1
  summary: The article describes the Awakari app, which allows users to create public
    or private 'interests' that can be subscribed to by others. It provides details
    on the app's features like unique IDs, active/inactive status, and expiration
    dates.
extraction_timestamp: '2025-06-15T22:04:35.870474Z'
fetch_status: success
fetched_at: '2025-06-15T22:04:35.870495Z'
found_in_posts:
- at://did:plc:odj22pn3oookfcayhqnn52av/app.bsky.feed.post/3lrn7nkcguoa2
language: en
medium: null
stage: evaluated
title: Awakari App
url: https://awakari.com/sub-details.html?id=FunctionalProgramming
word_count: 139
---

# Awakari App

Public

May be discovered and subscribed by other users.

Note that making a public interest private doesn't disconnect existing subscribers.

Create a new private interest for this.

ID

A unique short name useful for public interests.

Can't be changed once set.

A random name is set when not specified.

Max 36 symbols, ASCII letters, digits or dash.

Keep it secret for a private interest.

Create a new interest when id is compromised.

Active

Active interest filters the input stream.

Inactive interest doesn't get new events.

Count of simultaneously active user interests is limited. To create a new active interest or activate an existing one it may be necessary to increase the current user's limit.

Expire  A local date when the interest expires and becomes inactive. An interest never expires when this date is not set.