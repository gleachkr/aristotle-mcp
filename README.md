# Aristotle MCP Server

A minimal Model Context Protocol (MCP) server for the Aristotle API, enabling LLMs to prove theorems in Lean and formalize mathematical problems.

## Installation

This project uses `uv` for dependency management.

```bash
uv sync
```

## Configuration

You need an Aristotle API key. Set it in your environment:

```bash
export ARISTOTLE_API_KEY="your-api-key-here"
```

## Running the Server

Run the server using `uv`:

```bash
uv run main.py
```

This will start the MCP server over stdio.

## Tools

-   `prove_lean_file(file_path)`: Submit a Lean file for proving. Returns Project ID.
-   `prove_informal(file_path, formal_context_path)`: Submit a natural language problem. Returns Project ID.
-   `prove_lean_code(lean_code)`: Submit Lean code string. Returns Project ID.
-   `prove_informal_text(text, formal_context_path)`: Submit natural language string. Returns Project ID.
-   `get_project_status(project_id, save_solution_to)`: Check status and retrieve solution code.
-   `list_recent_projects()`: List recent projects.

## Resources

-   `aristotle://projects`: JSON list of recent projects.
-   `aristotle://projects/{project_id}`: Detailed status and content of a specific project.
