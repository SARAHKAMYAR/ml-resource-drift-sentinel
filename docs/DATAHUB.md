# DataHub integration boundary

The new CLI accepts a flat schema export and an optional list of upstream asset names. This deliberately keeps the monitoring logic independent of a particular metadata service response shape.

The original MCP implementation is preserved in `legacy/original_drift_check.py`. It is historical reference code, not a working setup guide for the new CLI. No live DataHub instance was available for validating that path during this revision.

## Export format

Normalize each dataset field into `{fieldPath: nativeDataType}` and save the result as JSON. Feed that file to `--schema`. Fetch every page before comparing; a truncated schema can look like removed columns. Preserve full nested field paths and reject duplicate paths. Treat a failed metadata lookup as an acquisition error, rather than an empty schema. An intentionally empty schema is valid input and reports all baseline fields as removed.

Pass a JSON array of upstream names through `--lineage`. Omitting it means lineage was not supplied; an empty array means the supplied export contained no upstream assets. Neither proves a local cause.

## Connecting an adapter later

1. Discover the deployed server's tools and inspect their input schemas.
2. Fetch and validate the complete schema. Normalize it into the export format above.
3. Pass it to `sentinel.core.assess` with the dataset URN as the stable identifier.
4. Keep observation state in a single-writer store, or replace it with transactional shared storage.
5. Make metadata mutation opt-in and capability-aware. Handle authorization and transport failures separately from schema findings.
6. Persist a write-back marker only after a successful mutation, so retries do not silently skip delivery or duplicate alerts.

The current core does not implement steps 1, 2, 5, or 6. In particular, `newly_opened` is an observation flag, not a durable write-back delivery guarantee.

The official server lists schema and lineage tools. Mutation availability depends on deployment and configuration; release notes describe entity description updates as Cloud-only. Check the deployed tool list before using the original append-description approach.

Sources checked during this revision:

- [Official DataHub MCP server](https://github.com/acryldata/mcp-server-datahub)
- [Official release notes](https://github.com/acryldata/mcp-server-datahub/releases)

Do not publish tokens or private schema exports. The included fixtures contain field metadata only and synthetic changes.
