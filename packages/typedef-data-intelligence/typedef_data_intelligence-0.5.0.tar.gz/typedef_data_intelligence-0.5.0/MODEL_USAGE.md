# Model Selection Guide

You can now easily switch between different LLM models for semantic analysis using environment variables or command arguments!

## Quick Start

### Show Current Settings

```bash
just backend-info
```

Output:

```
Current backend: kuzu
Current model: google/gemini-2.0-flash-exp

Available models:
  - google/gemini-2.0-flash-exp (default, fast)
  - google/gemini-2.5-flash-lite (lite version)
  - anthropic/claude-3.5-sonnet (most accurate)
  - gpt5, gpt4, gemini-flash (aliases)
```

## Using Different Models

### Via Environment Variable

```bash
# Set for your session
export LINEAGE_MODEL="anthropic/claude-3.5-sonnet"

# Now all loads use Claude
just load-demo kuzu
just run
cd dbt_projects/demo_finance && just load
```

### Via Command Argument

```bash
# One-off with specific model
just load-demo kuzu "anthropic/claude-3.5-sonnet"

# From dbt project
cd dbt_projects/demo_finance
just load kuzu "google/gemini-2.5-flash-lite"
just run kuzu "anthropic/claude-3.5-sonnet"
```

### Combine Backend and Model

```bash
# Load to PostgreSQL AGE with Claude
just load-demo postgres-age "anthropic/claude-3.5-sonnet"

# Load to ArcadeDB with Gemini Lite
just load-demo arcadedb "google/gemini-2.5-flash-lite"

# From dbt project with custom model
cd dbt_projects/demo_finance
just run kuzu "anthropic/claude-3.5-sonnet"
```

## Available Models

### Google Models (via OpenRouter)

**google/gemini-2.0-flash-exp** (default)

- Fast and cost-effective
- Great for most use cases
- Good balance of speed and accuracy

**google/gemini-2.5-flash-lite**

- Even faster, lighter
- Lower cost
- Good for simple schemas

### Anthropic Models

**anthropic/claude-3.5-sonnet**

- Most accurate
- Best for complex SQL
- Higher cost but better results

### Aliases (for convenience)

**gpt5, gpt4**

- Map to OpenAI GPT models
- Good general purpose

**gemini-flash**

- Alias for Gemini Flash

## Examples

### Development (Fast Iteration)

```bash
# Use fast model for quick testing
export LINEAGE_MODEL="google/gemini-2.5-flash-lite"
cd dbt_projects/demo_finance
just run
```

### Production (High Accuracy)

```bash
# Use Claude for best results
export LINEAGE_MODEL="anthropic/claude-3.5-sonnet"
cd dbt_projects/demo_finance
just run
```

### Mixed Approach

```bash
# Fast model for initial load
just load-demo kuzu "google/gemini-2.5-flash-lite"

# Then re-analyze specific models with Claude via CLI
uv run lineage load-dbt-full target/ \
    --model-filter "fct_" \
    --model "anthropic/claude-3.5-sonnet" \
    --verbose
```

## Cost Considerations

### By Speed/Cost

**Fastest/Cheapest** → **Slowest/Most Expensive**

1. `google/gemini-2.5-flash-lite`
2. `google/gemini-2.0-flash-exp`
3. `gpt4`
4. `anthropic/claude-3.5-sonnet`

### Recommendations

- **Development**: `google/gemini-2.5-flash-lite` or `google/gemini-2.0-flash-exp`
- **Testing**: `google/gemini-2.0-flash-exp` (default)
- **Production**: `anthropic/claude-3.5-sonnet` (best quality)
- **Complex SQL**: `anthropic/claude-3.5-sonnet` (handles edge cases)

## CLI Direct Usage

You can also call the CLI directly:

```bash
# With custom model
uv run lineage load-dbt-full path/to/target/ \
    --backend kuzu \
    --model "anthropic/claude-3.5-sonnet" \
    --verbose

# Filter specific models with custom model
uv run lineage load-dbt-full path/to/target/ \
    --backend kuzu \
    --model-filter "fct_" \
    --model "google/gemini-2.5-flash-lite" \
    --verbose
```

## Justfile Cheat Sheet

```bash
# Show current settings
just backend-info

# Load with default (gemini-2.0-flash-exp)
just load-demo kuzu

# Load with Claude
just load-demo kuzu "anthropic/claude-3.5-sonnet"

# Load with Gemini Lite
just load-demo kuzu "google/gemini-2.5-flash-lite"

# From dbt project
cd dbt_projects/demo_finance
just run kuzu "anthropic/claude-3.5-sonnet"
just load kuzu "google/gemini-2.5-flash-lite"

# Set default for session
export LINEAGE_MODEL="anthropic/claude-3.5-sonnet"
just run  # Uses Claude
```

---

**Now you have full control over both backend AND model selection!** 🎉
