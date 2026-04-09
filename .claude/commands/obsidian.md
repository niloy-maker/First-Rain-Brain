# /obsidian — Interact with Obsidian Notes

The Obsidian CLI is installed. Use the `obsidian` command to interact with notes.

## Discovery
To see all available subcommands, run any invalid command (e.g. `obsidian x`) — the CLI prints full usage.

## Syntax
Arguments use `key=value` form — no `--` flags:
```
obsidian <command> [key=value ...]
```

## Common subcommands
- `obsidian search query="." format=json` — list all files in the vault
- `obsidian search query=<text> format=json` — search notes by keyword
- `obsidian open file=<name>` — open a note in Obsidian (requires Obsidian to be running)
- For reading file contents, use the Read tool directly on the vault path instead

## Notes
- Use `format=json` when querying data so output is parseable
- `file=` resolves by name (like wikilinks); `path=` is exact
- Quote values with spaces: `file="My Note"`
