# Project Refactoring Plan: Independent Stage-Based Architecture

## Overview

Refactor the newsparser project from bulk processing to independent stages, where each stage processes items individually and stores outputs as Markdown files with frontmatter. This approach provides fault tolerance, easy debugging, and experimentation flexibility.

## Current Architecture Analysis

### Current Data Flow
```
Bluesky API → Parquet (bulk) → Anthropic API → Parquet (bulk) → HTML Reports
```

### Pain Points
1. **Bulk processing**: Single Parquet files mean losing all progress on failure
2. **Tight coupling**: Stages depend on exact file formats/locations
3. **Hard to debug**: Individual items buried in bulk files
4. **Poor experimentation**: Can't easily reprocess single items

## Proposed Refactoring: Stage-Based Architecture

### New Data Flow
```
Stage: collect    → .md per post
Stage: fetch      → .md per URL  
Stage: evaluate   → .md per article
Stage: report     → .md per day + HTML
```

## Stage Definitions

### **Stage: collect**
```python
class CollectStage:
    """Collects posts from Bluesky and stores individually"""
    input: BlueskyAPI + SearchConfig
    output: individual .md files per post
    location: stages/collect/YYYY-MM-DD/
```

**Output Format Example:**
```markdown
---
id: "at://did:plc:cnkcdjrvp5b27gqmdsbpbn5o/app.bsky.feed.post/3lrivlab6qc2x"
author: "james.montemagno.com"
created_at: "2024-12-06T15:45:00Z"
language: "latin"
engagement:
  likes: 12
  reposts: 3
  replies: 1
links:
  - "https://example.com/article"
tags:
  - "mcp"
  - "ai"
stage: "collected"
collected_at: "2024-12-06T16:00:00Z"
---

# Post Content

Check out this amazing MCP tool: https://example.com/article

This is going to change everything! #mcp #ai
```

### **Stage: fetch**
```python
class FetchStage:
    """Fetches full content from URLs found in posts"""
    input: collect stage .md files with links
    output: individual .md files per URL
    location: stages/fetch/YYYY-MM-DD/
```

**Output Format Example:**
```markdown
---
url: "https://example.com/article"
found_in_posts:
  - "at://did:plc:example/app.bsky.feed.post/123"
fetched_at: "2024-12-06T16:05:00Z"
fetch_status: "success"
word_count: 1543
title: "Revolutionary MCP Integration"
author: "John Developer"
domain: "example.com"
published_date: "2024-12-05T10:00:00Z"
stage: "fetched"
---

# Article Content

Revolutionary MCP Integration techniques are changing how we build AI applications...

[Full article content here]
```

### **Stage: evaluate**
```python
class EvaluateStage:
    """Evaluates content relevance using Anthropic API"""
    input: fetch stage .md files
    output: enhanced .md files with evaluation
    location: stages/evaluate/YYYY-MM-DD/
```

**Output Format Example:**
```markdown
---
url: "https://example.com/article"
# ... existing frontmatter from fetch stage ...
evaluation:
  is_mcp_related: true
  relevance_score: 0.85
  summary: "Article discusses advanced MCP integration patterns for AI applications"
  perex: "🚀 Game-changing MCP tricks that'll make your AI apps sing!"
  key_topics:
    - "Model Context Protocol"
    - "AI Integration"
    - "Development Patterns"
  evaluated_at: "2024-12-06T16:10:00Z"
  evaluator: "claude-3-5-sonnet-20241022"
stage: "evaluated"
---

# Article Content

[Same content as fetch stage, preserved]
```

### **Stage: report**
```python
class ReportStage:
    """Generates daily reports from evaluated content"""
    input: evaluate stage .md files
    output: report metadata + HTML files
    location: stages/report/YYYY-MM-DD/
```

**Output Format Example:**
```markdown
---
date: "2024-12-06"
total_posts: 45
total_urls: 23
evaluated_urls: 18
mcp_related_articles: 8
report_generated_at: "2024-12-06T16:15:00Z"
stage: "reported"
articles:
  - url: "https://example.com/article"
    relevance_score: 0.85
    title: "Revolutionary MCP Integration"
    perex: "🚀 Game-changing MCP tricks..."
---

# Daily Report Summary

Generated report for December 6, 2024 with 8 MCP-related articles.
```

## Benefits of This Approach

### 1. **Fault Tolerance**
- Each item processed individually
- Partial failures don't lose completed work
- Easy to resume where left off

### 2. **Easy Debugging**
- Each .md file is human-readable
- Clear progression through stages
- Individual items can be reprocessed

### 3. **Experimentation Friendly**
- Modify single items and reprocess
- A/B test different evaluation prompts
- Easy to cherry-pick interesting cases

### 4. **Simple Architecture**
```python
class Stage:
    def get_inputs(self) -> Iterator[Path]:
        """Find input files to process"""
    
    def process_item(self, input_path: Path) -> Path:
        """Process single item, return output path"""
    
    def run(self, date_filter: Optional[date] = None):
        """Process all pending items"""
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. **Create stage base classes**
   - `Stage` abstract base class
   - File discovery and processing logic
   - Progress tracking and resumption

2. **Markdown utilities**
   - Frontmatter parsing/writing
   - Content preservation between stages
   - Stage progression tracking

### Phase 2: Implement New Stages
1. **CollectStage**: Refactor from `BlueskyDataCollector`
2. **FetchStage**: Extract content fetching from evaluation
3. **EvaluateStage**: Refactor from `EvaluationProcessor`
4. **ReportStage**: Refactor from `ReportGenerator`

### Phase 3: CLI Integration
1. **Update commands**
   - `nsp collect` - run collect stage
   - `nsp fetch` - run fetch stage
   - `nsp evaluate` - run evaluate stage
   - `nsp report` - run report stage
   - `nsp run-all` - run all stages in sequence

2. **Add utilities**
   - `nsp status` - show stage progression for date
   - `nsp retry <stage> <item>` - reprocess specific item
   - `nsp clean <stage> <date>` - reset stage for date
   - `nsp list <stage>` - list items in stage

### Phase 4: Enhanced Features
1. **Parallel processing within stages**
2. **Stage dependency validation**
3. **Progress reporting and metrics**

## Directory Structure

```
stages/
├── collect/
│   └── 2024-12-06/
│       ├── post_abc123.md
│       ├── post_def456.md
│       └── ...
├── fetch/
│   └── 2024-12-06/
│       ├── url_hash1.md
│       ├── url_hash2.md
│       └── ...
├── evaluate/
│   └── 2024-12-06/
│       ├── url_hash1.md  # enhanced with evaluation
│       ├── url_hash2.md
│       └── ...
└── report/
    └── 2024-12-06/
        ├── report_meta.md
        └── report.html
```

## CLI Commands

### Stage Commands
```bash
# Run individual stages
nsp collect --date 2024-12-06
nsp fetch --date 2024-12-06
nsp evaluate --date 2024-12-06
nsp report --date 2024-12-06

# Run all stages in sequence
nsp run-all --date 2024-12-06

# Utility commands
nsp status --date 2024-12-06           # Show progress across all stages
nsp list collect --date 2024-12-06    # List items in collect stage
nsp retry evaluate url_hash1.md       # Reprocess specific item
nsp clean fetch --date 2024-12-06     # Clear fetch stage for date
```

## File Naming Conventions

### Posts (collect stage)
- Pattern: `post_{short_id}.md`
- Example: `post_3lrivlab6qc2x.md`
- Short ID extracted from AT protocol URI

### URLs (fetch/evaluate stages)
- Pattern: `url_{url_hash}.md`
- Example: `url_a1b2c3d4.md`
- Hash based on URL for deduplication

### Reports (report stage)
- Pattern: `report_meta.md` + `report.html`
- Single metadata file + HTML output per date

## Benefits Over Current Architecture

1. **Granular Control**: Process/reprocess individual items
2. **Human-Readable**: All data in .md format with frontmatter
3. **Fault-Tolerant**: No loss of work on partial failures
4. **Debuggable**: Easy to trace individual items through pipeline
5. **Flexible**: Easy to modify stages independently
6. **Experimentation**: Test changes on subsets of data
7. **No Migration Needed**: Start fresh with new architecture

## Data Migration Strategy

**Decision: No migration needed**
- Current dataset is small enough to re-collect
- Fresh start with new architecture is cleaner
- Avoids complexity of format conversion
- Opportunity to improve data quality from the beginning

This refactoring transforms the current bulk-processing pipeline into a resilient, item-by-item system that's much easier to debug, modify, and experiment with. Each stage becomes a simple class that reads input files and produces output files, making the entire system more modular and maintainable.