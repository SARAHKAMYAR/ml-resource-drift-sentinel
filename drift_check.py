import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CMD = "/Users/sara/miniconda3/envs/datahub/bin/mcp-server-datahub"
URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.customers,PROD)"
BASELINE = Path("baseline_schema.json")
MEMORY = Path("drift_memory.json")

def load_memory():
    return json.loads(MEMORY.read_text()) if MEMORY.exists() else {}

def update_memory(field_name):
    mem = load_memory()
    mem[field_name] = mem.get(field_name, 0) + 1
    MEMORY.write_text(json.dumps(mem, indent=2))
    return mem[field_name]

async def get_schema(session):
    result = await session.call_tool("list_schema_fields", arguments={"urn": URN, "limit": 100})
    data = json.loads(result.content[0].text)
    fields = data.get("fields", data if isinstance(data, list) else [])
    return {f["fieldPath"]: f.get("nativeDataType", "unknown") for f in fields}

async def get_upstream_lineage(session):
    result = await session.call_tool("get_lineage", arguments={"urn": URN})
    data = json.loads(result.content[0].text)
    upstreams = data.get("upstreams", {}).get("searchResults", [])
    names = []
    for u in upstreams:
        entity = u["entity"]
        name = entity.get("properties", {}).get("name") or entity.get("dataFlow", {}).get("properties", {}).get("name") or entity.get("urn")
        names.append(name)
    return names

async def run(mode):
    params = StdioServerParameters(
        command=CMD,
        env={"DATAHUB_GMS_URL": "http://localhost:8080", "TOOLS_IS_MUTATION_ENABLED": "true"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            schema = await get_schema(session)

            if mode == "snapshot":
                BASELINE.write_text(json.dumps(schema, indent=2))
                print(f"Baseline saved: {len(schema)} fields -> {list(schema.keys())}")
                return

            baseline = json.loads(BASELINE.read_text())
            removed = sorted(set(baseline) - set(schema))
            changed = sorted(f for f in baseline if f in schema and schema[f] != baseline[f])

            if not removed and not changed:
                print("No drift detected.")
                return

            upstream_sources = await get_upstream_lineage(session)
            if upstream_sources:
                attribution = f"May be INHERITED from upstream pipeline(s): {', '.join(upstream_sources)}"
            else:
                attribution = "No upstream pipeline found — drift appears LOCAL to this table"

            all_changed_fields = removed + changed
            occurrence_notes = []
            for field_name in all_changed_fields:
                count = update_memory(field_name)
                if count > 1:
                    occurrence_notes.append(f"{field_name} (seen {count}x — recurring pattern)")
                else:
                    occurrence_notes.append(f"{field_name} (first occurrence)")

            if any("recurring" in n for n in occurrence_notes):
                recommendation = "RECOMMENDATION: recurring drift — escalate to pipeline owner, not a one-off fix"
            else:
                recommendation = "RECOMMENDATION: first occurrence — monitor next run before escalating"

            msg = (f"DRIFT DETECTED - removed fields: {removed}, changed types: {changed}\n"
                   f"{attribution}\n"
                   f"History: {'; '.join(occurrence_notes)}\n"
                   f"{recommendation}")
            print(msg)

            await session.call_tool("update_description", arguments={
                "entity_urn": URN,
                "operation": "append",
                "description": f"\n\n⚠️ {msg}",
            })
            print("\nFlag written back to DataHub — check the customers dataset page.")

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "check"))
