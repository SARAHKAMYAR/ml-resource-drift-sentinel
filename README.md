# ML Resource Drift Sentinel

An agent that catches silent schema drift in production data before it silently degrades a downstream ML model — and writes what it learns directly back into DataHub's metadata graph, so the next person or agent inherits the knowledge instead of rediscovering the problem.

Built for **Build with DataHub: The Agent Hackathon** — Production ML Agents category.

## Why This Is Different

Most drift detectors tell you something changed. This one tells you whether you've seen it before, where it probably came from, and writes that knowledge into the same graph the next person will already be looking at.

**Detect + Analyze — not just "what changed" but "where it came from."**
Grounded in current MLOps research (Leest et al., 2025, *"Tracing Distribution Shifts with Causal System Maps"*), most monitoring tools report a shift as an undifferentiated alarm. This agent uses DataHub's lineage graph to distinguish drift local to a table from drift inherited from an upstream pipeline, so the alert routes toward the team actually responsible.

**Knowledge — the graph remembers, so the system gets smarter over time.**
The agent tracks occurrence history and distinguishes a first-time anomaly from a recurring pattern. A field that drifts once is noise; a field that drifts repeatedly signals the pipeline itself is unreliable.

**Write-back — DataHub as shared memory, not a side channel.**
Every finding — the drift, its likely origin, and its history — gets written back into DataHub itself, rather than a log file or a Slack message only one person sees.

This applies a lightweight version of the MAPE-K loop (Monitor–Analyze–Plan–Execute–Knowledge, IBM autonomic computing research) to ML data drift specifically, using DataHub's graph as the substrate for both the Analyze and Knowledge stages.

## How It Works

1. **Snapshot** — captures a dataset's schema via DataHub's MCP Server (`list_schema_fields`) as a known-good baseline.
2. **Detect** — on each run, re-fetches the live schema and diffs it against the baseline.
3. **Diagnose** — checks the dataset's upstream lineage (`get_lineage`) to determine whether drift is local or inherited from a pipeline.
4. **Learn** — tracks how often each field has drifted in a local memory file, distinguishing first occurrences from recurring patterns.
5. **Write back** — appends a structured alert (what changed, likely origin, history, recommendation) directly onto the dataset's description in DataHub (`update_description`).

## Demo

Demonstrated against a real e-commerce `customers` table — tagged PII and SOC2 Auditable, fed by a live Spark pipeline (`import_table_customers_to_snowflake`) — the kind of high-stakes table a real ML feature pipeline would depend on.

## Setup

Requires Python 3.11 (not 3.14 — see note below) and Docker.

```bash
# 1. Create environment
conda create -n datahub python=3.11 -y
conda activate datahub

# 2. Install DataHub
pip install acryl-datahub
datahub docker quickstart
datahub init
datahub datapack load showcase-ecommerce

# 3. Install and run the MCP Server
pip install mcp-server-datahub
export DATAHUB_GMS_URL=http://localhost:8080
export TOOLS_IS_MUTATION_ENABLED=true

# 4. Run the agent
python3 drift_check.py snapshot   # capture baseline
python3 drift_check.py check      # detect drift, diagnose, learn, write back
```

**Note:** if `pip install acryl-datahub` fails with a `pydantic-core` build error, your Python version is too new (3.14+). Use Python 3.11 via conda as shown above.

## Tech Stack

DataHub, DataHub MCP Server (Model Context Protocol), Python, Snowflake (sample data platform)

## License

Apache 2.0 — see LICENSE file.
