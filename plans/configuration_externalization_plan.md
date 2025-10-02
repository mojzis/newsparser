# Configuration Externalization and Prompt Versioning Plan

## Overview

This plan outlines the restructuring of the newsparser project to support:
1. GitHub Actions deployment with externalized configuration
2. Prompt and model versioning with experimental branches
3. A/B testing framework for prompts and models
4. Foundation for future library transformation

## Current State Analysis

### Configuration Distribution
- **Environment Variables**: API keys, credentials in `.env`
- **Hardcoded Values**: Prompts, model names, paths, limits
- **YAML Files**: Search configurations only
- **Python Code**: Mixed configuration and logic

### Key Issues
- Prompts are hardcoded in `anthropic_client.py`
- No versioning for prompts or their outputs
- Configuration scattered across multiple files
- Difficult to experiment with different settings

## Proposed Architecture

```
newsparser/
├── config/
│   ├── base/              # Default configurations
│   │   ├── app.yaml       # Application settings
│   │   ├── models.yaml    # Model configurations
│   │   ├── prompts.yaml   # Default prompts
│   │   └── searches.yaml  # Search definitions
│   ├── experiments/       # Experimental branches
│   │   ├── experiment_001_prompt_v2.yaml
│   │   ├── experiment_002_claude_sonnet.yaml
│   │   ├── experiment_003_combined_test.yaml
│   │   └── README.md
│   └── versions/          # Prompt & model version history
│       ├── prompts_v1.0.yaml
│       ├── prompts_v1.1.yaml
│       ├── models_v1.0.yaml
│       └── README.md
```

## Key Design Principles

### Experimental Branch Approach
Instead of traditional dev/staging/prod environments, we use **experimental branches** that allow:

1. **Flexible Experimentation**: Create branches for testing specific changes (new prompts, different models, combined changes)
2. **Easy Comparison**: Compare any branch against baseline or other branches
3. **Safe Testing**: Experiments run on sample data without affecting production
4. **Quick Iteration**: Easy to create, test, and abandon or promote experiments

### Branch Examples:
- `base` - Default configuration (replaces "production")
- `experiment_001_prompt_v2` - Test improved prompt wording
- `experiment_002_claude_sonnet` - Test different model
- `experiment_003_combined` - Test prompt + model changes together

### A/B Testing Framework
- Run experiments on percentage of data (e.g., 10% sample)
- Track multiple metrics (relevance_score, cost, processing_time)
- Compare results statistically
- Promote successful experiments to base configuration

## Implementation Phases

### Phase 1: Configuration Externalization (Week 1)

**Objective**: Extract all configuration from code into structured YAML files.

**Tasks**:
1. Create configuration schema and validation
2. Extract application settings to `config/base/app.yaml`
3. Move prompts to `config/base/prompts.yaml`
4. Implement configuration loader with environment override support
5. Update all code references to use configuration system
6. Add configuration validation on startup

**Deliverables**:
- Configuration management module
- YAML configuration files
- Updated application code
- Configuration documentation

### Phase 2: Prompt & Model Versioning System (Week 2)

**Objective**: Enable prompt and model experimentation with version tracking.

**Tasks**:
1. Design prompt and model versioning schema
2. Add prompt/model version to evaluation metadata
3. Create model configuration management
4. Create prompt and model version management CLI commands
5. Implement experimental branch system
6. Add A/B testing capability for prompts and models
7. Add prompt and model performance analytics
8. Create experimentation notebook

**Deliverables**:
- Prompt and model versioning system
- Experimental branch system
- CLI commands for prompt and model management
- Analytics dashboard for prompt/model performance
- Documentation for experimentation workflow

### Phase 3: Experimental Framework & GitHub Actions (Week 3)

**Objective**: Enable A/B testing of prompts and models with automated deployment.

**Tasks**:
1. Create experimental branch system
2. Implement A/B testing framework for prompts and models
3. Add experiment tracking and comparison tools
4. Create GitHub Actions workflow with experiment support
5. Set up GitHub Secrets for sensitive data
6. Add experiment monitoring and reporting
7. Document experimentation workflow

**Deliverables**:
- Experimental branch system
- A/B testing framework
- GitHub Actions workflow with experiment support
- Experiment comparison tools
- Documentation for running experiments

### Phase 4: Library Foundation (Week 4)

**Objective**: Refactor architecture to support future library transformation.

**Tasks**:
1. Create clear API boundaries
2. Separate core functionality from CLI
3. Design plugin architecture for custom processors
4. Create example configurations
5. Write library usage documentation
6. Plan public API surface

**Deliverables**:
- Refactored module structure
- API design document
- Example configurations
- Future roadmap

## Configuration Schema Design

### Application Configuration (`app.yaml`)
```yaml
version: "1.0"
metadata:
  name: "newsparser"
  description: "Bluesky MCP Monitor"

paths:
  stages_base: "stages"
  templates: "src/templates"
  data_legacy: "data"
  reports: "reports"
  
processing:
  fetch_lookback_days: 10
  min_relevance_score: 0.3
  max_concurrent_requests: 10
  
# Model configuration moved to models.yaml
# This allows for easier model experimentation
processing:
  default_model_config: "mcp_evaluator_v1"
  enable_model_experiments: true
    
ui:
  site_title: "MCP Monitor"
  site_tagline: "Daily digest of Model Context Protocol mentions"
  theme: "default"
```

### Prompt Configuration (`prompts.yaml`)
```yaml
version: "1.0"
metadata:
  created: "2024-01-01"
  author: "system"
  description: "Default MCP evaluation prompts"

prompts:
  mcp_evaluation:
    name: "MCP Article Evaluation"
    version: "1.0"
    model_config:
      temperature: 0
      max_tokens: 500
    template: |
      Analyze this article for relevance to Model Context Protocol (MCP).
      
      MCP is a protocol for AI tool integration that allows language models 
      to access external tools and data sources.
      
      Article:{title_part}{hints_part}
      Content:
      {content}
      
      Evaluate and respond with JSON containing:
      1. is_mcp_related (boolean)
      2. relevance_score (0.0-1.0)
      3. summary (string, max 200 chars)
      4. perex (string, max 150 chars)
      5. key_topics (array of strings)
      6. content_type (string)
      7. language (string)
      
      Respond only with valid JSON.
    
    variables:
      - name: title_part
        required: false
      - name: hints_part
        required: false
      - name: content
        required: true
```

## Data Schema Updates

### Evaluation Data Enhancement
Add to evaluation records:
```python
class EvaluationResult(BaseModel):
    # Existing fields...
    prompt_version: str  # Version of prompt used
    prompt_name: str     # Name of prompt template
    model_version: str   # Anthropic model used
    config_version: str  # Configuration version
```

## CLI Command Additions

```bash
# Configuration management
poetry run nsp config validate
poetry run nsp config show [--env production]
poetry run nsp config diff development production

# Prompt management
poetry run nsp prompts list
poetry run nsp prompts show mcp_evaluation
poetry run nsp prompts create --from mcp_evaluation --version 1.1
poetry run nsp prompts test mcp_evaluation --sample-file sample.md
poetry run nsp prompts compare v1.0 v1.1 --date 2024-01-01

# A/B testing
poetry run nsp prompts ab-test --prompt-a v1.0 --prompt-b v1.1 --sample-size 100
```

## Environment Variable Structure

```bash
# Required secrets (GitHub Secrets)
ANTHROPIC_API_KEY=sk-...
BLUESKY_HANDLE=...
BLUESKY_APP_PASSWORD=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...

# Configuration selection
NSP_ENVIRONMENT=production  # or development, staging
NSP_CONFIG_PATH=/path/to/config  # Optional override

# Feature flags
NSP_ENABLE_PROMPT_AB_TEST=true
NSP_ENABLE_DEBUG_LOGGING=false
```

## Migration Strategy

1. **Backward Compatibility**: Keep existing functionality working during migration
2. **Incremental Updates**: Migrate one component at a time
3. **Feature Flags**: Use flags to enable new configuration system
4. **Dual Running**: Run old and new systems in parallel initially
5. **Validation**: Extensive testing before switching over

## Success Criteria

- [ ] All configuration externalized from code
- [ ] Prompts versioned and tracked in data
- [ ] GitHub Actions running daily successfully
- [ ] Configuration changes require no code changes
- [ ] Prompt experimentation documented and easy
- [ ] Clear path to library transformation

## Risk Mitigation

1. **Data Loss**: Backup all data before migration
2. **Service Disruption**: Use feature flags for gradual rollout
3. **Configuration Errors**: Implement strict validation
4. **Secret Exposure**: Use GitHub Secrets, never commit secrets
5. **Prompt Regression**: A/B test new prompts before full deployment

## Next Steps

1. Review and approve this plan
2. Set up development environment for testing
3. Begin Phase 1 implementation
4. Weekly progress reviews
5. Adjust plan based on findings