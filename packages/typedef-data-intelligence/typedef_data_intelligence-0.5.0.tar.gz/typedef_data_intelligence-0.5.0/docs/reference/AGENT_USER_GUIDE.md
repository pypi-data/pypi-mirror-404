# Data Intelligence Agent User Guide

This guide explains the different AI agents available in the typedef Data Intelligence Platform, when to use each one, their capabilities, and limitations.

## Quick Reference

| Agent                        | Best For                                            | Can Modify Data? | Access Level        |
| ---------------------------- | --------------------------------------------------- | ---------------- | ------------------- |
| **Data Analyst**             | Business questions, reports, visualizations         | No               | Semantic views only |
| **Data Investigator**        | Troubleshooting data discrepancies, error diagnosis | No               | Full read access    |
| **Data Insights**            | Understanding architecture, pipeline health         | No               | Full read access    |
| **Data Engineer Copilot**    | Building/modifying dbt models (interactive)         | Yes              | Full access         |
| **Data Engineer Reconciler** | Autonomous ticket processing                        | Yes              | Full access         |

---

## Data Analyst

### Analyst Overview

The Data Analyst is your go-to agent for answering business questions using data. It works exclusively with **semantic views** (Snowflake Semantic Models, etc.) to provide curated, validated analytics without requiring SQL knowledge.

### When to Use the Analyst

- Answering business questions about metrics (ARR, revenue, churn, etc.)
- Creating visualizations and charts
- Building reports for stakeholders
- Exploring available metrics and dimensions
- Routine analytics tasks

### Analyst Capabilities

- Query semantic views using natural language (no SQL required)
- Create visualizations: bar charts, line charts, pie charts, scatter plots, area charts
- Generate HTML reports with multiple sections
- Remember your preferences (date ranges, chart types, filters)
- Create tickets when data doesn't meet your needs

### Analyst Limitations

- **Only works with existing semantic views** - cannot access raw tables or create new semantic views
- **Restricted to curated marts** - typically limited to the `marts` schema
- **Read-only** - cannot modify data or code
- **Requires semantic views to exist** - if the metric you need isn't in a semantic view, you'll need to request it via ticket

### Analyst Sample Prompts

```text
"Show me ARR by customer segment for 2024"

"What were our top 10 customers by revenue last quarter?"

"Create a line chart of monthly recurring revenue over the past 12 months"

"Break down pipeline value by sales stage and region"

"Generate a report comparing this quarter's ARR to last quarter"

"I always want to see the last 90 days of data by default"
```

### When the Analyst Needs More

If the Data Analyst can't answer your question because a metric or dimension doesn't exist in semantic views, it will:

1. Explain exactly what's missing
2. Ask if you'd like to create a ticket for the Data Engineer
3. Create a detailed ticket with the business use case and required measures/dimensions

---

## Data Investigator

### Investigator Overview

The Data Investigator specializes in tracking down the root cause of data discrepancies and diagnosing operational issues. When your numbers don't match expectations or a pipeline fails, this agent traces the data flow to find where things went wrong.

### When to Use the Investigator

- Data doesn't match what you expected
- Numbers changed unexpectedly
- Pipeline or job failures
- Reconciling differences between reports
- Understanding why calculations produce unexpected results
- Checking if data is fresh and pipelines ran successfully

### Investigator Capabilities

- Trace data flow upstream to find where issues originate
- Analyze how metrics are calculated (aggregation logic, joins, filters)
- Understand grain mismatches (e.g., summing at subscription vs customer level)
- Diagnose job failures and error messages
- Compare expected vs actual calculations
- Create detailed tickets with root cause analysis
- Visualize data flow with diagrams

### Investigator Limitations

- **Read-only** - cannot fix issues, only diagnose them
- **Creates tickets for fixes** - remediation requires Data Engineer
- **Hypothesis-driven** - works best when you can describe what you expected vs what you got

### Investigator Sample Prompts

```text
"Why is ARR showing $10M when I expected $12M?"

"This customer's revenue doesn't match what's in Salesforce"

"The total in fct_revenue doesn't equal the sum of its parts"

"Something changed in our MRR calculation last Tuesday"

"Why did fct_revenue fail last night?"

"Trace where the exchange_rate value comes from in fct_international_revenue"

"Which jobs are currently blocked or failing?"
```

### Investigator Workflow

When you report an issue, the Investigator will:

1. Ask clarifying questions (what did you expect vs what did you see?)
2. Search for relevant models using the knowledge graph
3. Analyze grain, measures, and calculation logic
4. Trace upstream dependencies
5. Validate a specific hypothesis with data
6. Document findings and create a ticket if a fix is needed

---

## Data Insights

### Insights Overview

The Data Insights agent is your guide to understanding your data architecture and monitoring overall health. It explains how models work, how tables connect, surfaces patterns you might not have known to ask about, and provides visibility into pipeline status.

### When to Use Insights

- Understanding what a model does and why
- Learning how tables join together
- Discovering available measures and dimensions
- Getting architecture explanations for new team members
- Understanding the "why" behind data design decisions
- Monitoring pipeline health and data freshness

### Insights Capabilities

- Explain models in plain business language
- Show how tables relate and join
- Surface measures, dimensions, and grain for any model
- Create architecture diagrams (Mermaid)
- Proactively mention related patterns you might find useful
- Find models that commonly join together (join clusters)
- Monitor job status and identify health trends

### Insights Limitations

- **Read-only** - explains but doesn't modify
- **Focuses on education** - not for running analytics queries
- **Knowledge graph-based** - relies on pre-analyzed metadata

### Insights Sample Prompts

```text
"Explain what fct_arr_reporting does"

"How do dim_customers and fct_subscriptions join together?"

"What measures are available for revenue analysis?"

"Show me the data model for our finance domain"

"What's the grain of fct_pipeline?"

"Which models should I use for customer churn analysis?"

"What are the key dimensions I can filter by in our ARR models?"

"Show me the health of our pipeline over the past 7 days"
```

### What to Expect from Insights

The Insights agent acts as a teacher:

- Explains concepts in business terms, not just technical jargon
- Provides context about why things are designed a certain way
- Creates diagrams to visualize relationships
- Proactively mentions related models or patterns you might find useful

---

## Data Engineer Copilot

### Copilot Overview

The Data Engineer Copilot is an interactive development partner for building and modifying dbt models. Unlike the read-only agents, it can actually make changes to your code—but always with your approval first.

### When to Use the Copilot

- Adding new columns or measures to existing models
- Creating new dbt models
- Refactoring SQL for better performance
- Fixing bugs in model logic
- Updating model dependencies
- Creating new semantic views

### Copilot Capabilities

- Full read/write access to dbt project files
- Git operations (branch, commit, push)
- Run dbt commands (compile, test, build)
- Execute SQL queries for validation
- Impact analysis before making changes
- Create semantic views that the Analyst can then use

### Copilot Limitations

- **Requires user approval** - always asks before making changes
- **Two-stage workflow** - confirms before code changes, then again before git operations
- **Never commits to main/master** - always creates feature branches
- **Interactive only** - designed for pair programming, not autonomous work

### Copilot Sample Prompts

```text
"Add customer_segment to fct_revenue"

"Create a new model for customer lifetime value"

"Refactor fct_arr to use an incremental materialization"

"Fix the join in fct_pipeline - it's duplicating rows"

"Add a test to ensure mrr is never negative"

"Update fct_subscriptions to include the cancellation_reason"

"Create a semantic view for ARR analysis with product_line dimension"
```

### Copilot Workflow

The Copilot follows a strict two-stage workflow:

#### Stage 1: Planning

1. Analyzes your request using the knowledge graph
2. Checks downstream impact
3. Presents a complete plan
4. **Waits for your approval** before making any changes

#### Stage 2: Implementation

1. Makes the code changes
2. Runs dbt tests
3. Shows results
4. **Waits for approval** before git operations
5. Creates feature branch and commits

### Key Difference from Other Agents

The Copilot is the only interactive agent that can modify code. Use it when you need to:

- Actually implement changes (not just propose them)
- Work alongside an AI pair programmer
- Get help with the technical implementation
- Create new semantic views for the Analyst to use

---

## Data Engineer Reconciler

### Reconciler Overview

The Data Engineer Reconciler runs autonomously as a daemon to process tickets created by other agents. It picks up work from the ticket queue and implements solutions without requiring interactive oversight.

### When the Reconciler Is Used

This agent is **not used directly by users**. Instead:

1. Other agents (Analyst, Investigator, Insights) create tickets
2. The Reconciler daemon picks up tickets automatically
3. It implements fixes, tests them, and submits PRs
4. It updates tickets with progress and completion status

### Reconciler Capabilities

- All capabilities of the Copilot (file/git/dbt operations)
- Autonomous operation without user interaction
- Ticket lifecycle management
- Proactive health monitoring (creates new tickets for related issues)

### Reconciler Limitations

- **Not interactive** - processes tickets from the queue
- **Requires well-specified tickets** - needs clear requirements to work autonomously
- **May request clarification** - will add comments and reassign if blocked

### How Tickets Flow Through the Reconciler

```text
1. User asks Analyst: "Show me ARR by product line"
2. Analyst discovers: No product_line dimension in semantic view
3. Analyst creates ticket: "Add product_line dimension to sv_arr"
4. Reconciler picks up ticket
5. Reconciler implements the change, tests it, creates PR
6. Reconciler updates ticket to "in_review"
7. Developer reviews and merges PR
8. Reconciler is notified, closes ticket
```

---

## Choosing the Right Agent

### Decision Flowchart

```text
What do you need?
│
├─ Answer a business question
│  └─ Is it about data architecture or actual data?
│     ├─ Data architecture/how things work → Data Insights
│     └─ Actual data/metrics/reports → Data Analyst
│
├─ Troubleshoot an issue
│  └─ Data Investigator (handles both operational and data issues)
│
└─ Make changes to the codebase
   └─ Data Engineer Copilot
```

### Common Scenarios

| Scenario                                               | Best Agent            |
| ------------------------------------------------------ | --------------------- |
| "What was our ARR last month?"                         | Data Analyst          |
| "Why is ARR different from what I calculated?"         | Data Investigator     |
| "How does ARR get calculated in our models?"           | Data Insights         |
| "Did the ARR model run successfully?"                  | Data Investigator     |
| "Add a new ARR breakdown by region"                    | Data Engineer Copilot |
| "Create a semantic view so I can query ARR by product" | Data Engineer Copilot |

---

## Tips for Best Results

### Be Specific

- **Good**: "Show me ARR by customer segment for enterprise customers in Q4 2024"
- **Less Good**: "Show me some revenue data"

### Provide Context

- Mention what you expected vs what you're seeing
- Reference specific models, tables, or timeframes when you know them
- Explain the business context (why you need this)

### Use the Right Agent

- Don't ask the Analyst to debug pipeline failures (use Investigator)
- Don't ask the Investigator for routine reports (use Analyst)
- Don't expect read-only agents to fix code (use Copilot)
- Need a new semantic view? Ask the Copilot to create it, then use the Analyst to query it

### Trust the Ticket System

When an agent creates a ticket, it includes:

- Detailed business context
- Technical requirements
- Priority based on your urgency

This information helps the engineering team prioritize and implement the right solution.
