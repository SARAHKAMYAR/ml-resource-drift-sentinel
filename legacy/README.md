# Original DataHub prototype

This folder preserves the submitted prototype for reference. It is not the supported entry point.
It contains a machine-specific executable path and dataset URN, assumes particular MCP response
shapes, counts repeated observations as occurrences, and appends descriptions on every drift check.
The original seeded memory has not been carried into the new incident store.

The supported CLI compares exported JSON schemas. Live MCP polling and metadata write-back are
not wired into the new core yet. See `docs/DATAHUB.md` for the integration boundary.
