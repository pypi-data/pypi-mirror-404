"""Agent placeholder content for the TUI chat interface."""

# Agent placeholder content: introductions and sample prompts
AGENT_PLACEHOLDERS = {
    "analyst": {
        "title": "Data Analyst",
        "intro": "Your friendly neighborhood number cruncher. I turn your business questions into charts, reports, and insights - no SQL wizardry required on your part.",
        "prompts": [
            "What semantic views are available?",
            "Show me ARR by customer segment for the last quarter",
            "Create a line chart of monthly revenue trends",
            "Show me active user trends over the last year",
        ],
    },
    "investigator": {
        "title": "Data Investigator",
        "intro": "Something fishy in your data? I'm on the case. When numbers don't add up or pipelines go bump in the night, I trace the breadcrumbs back to the source.",
        "prompts": [
            "Why is ARR showing $10M when I expected $12M?",
            "Trace where the revenue value comes from in fct_revenue",
            "Which pipelines failed in the last 24 hours?",
            "For November 2025, why is the ARR negative? That shouldn't be possible.",
        ],
    },
    "insights": {
        "title": "Data Insights",
        "intro": "Think of me as your data tour guide. I know where everything lives, how it connects, and why it was built that way. New to the codebase? Let's explore together.",
        "prompts": [
            "Can you give me a high-level overview of our data architecture?",
            "How do dim_customers and fct_subscriptions join?",
            "What measures are available for revenue analysis?",
            "Show me the data model for the finance domain",
        ],
    },
    "copilot": {
        "title": "Data Engineer Copilot",
        "intro": "Your pair programming buddy for all things dbt. I write the code, you call the shots. Every change gets your approval first - I'm helpful, not reckless.",
        "prompts": [
            "Add customer_segment to fct_revenue",
            "Create a new model for customer lifetime value",
            "The join in fct_pipeline is duplicating rows, can you fix it?",
            "We have daily, weekly, monthly active users in our reporting, can you add quarterly active users?",
        ],
    },
}
