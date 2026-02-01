#!/usr/bin/env python3
"""
Benchmarks for MCP Context Graph.

Measures:
1. Context Efficiency: Minified graph size vs. raw source files
2. Query Performance: Time to execute common queries
3. Indexing Speed: Time to ingest projects of various sizes

Usage:
    uv run python benchmarks/run_benchmarks.py /path/to/project
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

OPENROUTER_API_KEY = ""  # Set via env var or paste here
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_REGISTRY = {
    "gpt-5.2": {
        "input": 2.50,
        "output": 10.00,
        "model": "openai/gpt-5.2",
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "model": "openai/gpt-4o-mini",
    },
    "claude-sonnet-4.5": {
        "input": 3.00,
        "output": 15.00,
        "model": "anthropic/claude-4.5-sonnet",
    },
    "gemini-2.5-pro": {
        "input": 3.50,
        "output": 10.50,
        "model": "google/gemini-2.5-pro",
    },
}

_token_cache: dict[tuple[str, str], int] = {}


def get_api_key() -> str:
    """Get OpenRouter API key from global var or environment."""
    import os
    return OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")


def count_tokens_openrouter(text: str, model: str) -> int:
    """
    Count tokens via OpenRouter API using chat completions with max_tokens=1.

    Args:
        text: The text to tokenize
        model: OpenRouter model identifier (e.g., "openai/gpt-5.2")

    Returns:
        Token count from usage.prompt_tokens in API response

    Raises:
        RuntimeError: If API call fails or key not set
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key not set. Set OPENROUTER_API_KEY env var or "
            "edit OPENROUTER_API_KEY in benchmarks/run_benchmarks.py"
        )

    # Check cache first (use hash of text for large content)
    cache_key = (str(hash(text)), model)
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    # Truncate text if too long (most models handle up to 128k tokens)
    max_chars = 500_000  # ~125k tokens at 4 chars/token
    truncated_text = text[:max_chars] if len(text) > max_chars else text

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": truncated_text}],
        "max_tokens": 16,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        req = Request(
            OPENROUTER_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
            prompt_tokens = data.get("usage", {}).get("prompt_tokens", 0)

            # Scale up if we truncated
            if len(text) > max_chars:
                ratio = len(text) / max_chars
                prompt_tokens = int(prompt_tokens * ratio)

            _token_cache[cache_key] = prompt_tokens
            return prompt_tokens

    except URLError as e:
        raise RuntimeError(f"OpenRouter API error for {model}: {e}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Failed to parse OpenRouter response: {e}")


def count_tokens_for_model(text: str, model_name: str) -> int:
    """
    Count tokens for a specific model using OpenRouter API.

    Args:
        text: The text to tokenize
        model_name: Model name from MODEL_REGISTRY

    Returns:
        Exact token count from API
    """
    config = MODEL_REGISTRY.get(model_name, {})
    openrouter_model = config.get("model", "openai/gpt-4o")
    return count_tokens_openrouter(text, openrouter_model)


def format_bytes(size: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def measure_raw_source(project_path: Path, extensions: set[str]) -> tuple[int, int, str]:
    """
    Measure total size and collect content of source files.

    Returns:
        Tuple of (total_bytes, file_count, combined_content)
    """
    total_bytes = 0
    file_count = 0
    all_content: list[str] = []

    for file_path in project_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in extensions:
            continue
        # Skip common excluded directories
        parts = file_path.parts
        if any(p in parts for p in ["node_modules", "__pycache__", ".git", ".venv", "venv", "dist", "build"]):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            total_bytes += len(content.encode("utf-8"))
            all_content.append(content)
            file_count += 1
        except OSError:
            pass

    return total_bytes, file_count, "\n".join(all_content)


def run_benchmarks(project_path: Path) -> dict:
    """Run all benchmarks on the given project."""
    # Import here to measure import time
    import_start = time.perf_counter()
    from mcp_context_graph.ingest.ingestor import Ingestor
    import_time = time.perf_counter() - import_start

    results = {
        "project_path": str(project_path),
        "import_time_ms": import_time * 1000,
    }

    # Measure raw source size and collect content
    extensions = {".py", ".ts", ".js", ".tsx", ".jsx"}
    raw_bytes, file_count, raw_content = measure_raw_source(project_path, extensions)
    results["raw_source_bytes"] = raw_bytes
    results["raw_source_files"] = file_count
    results["raw_content"] = raw_content

    # Initialize ingestor
    init_start = time.perf_counter()
    ingestor = Ingestor(project_path)
    init_time = time.perf_counter() - init_start
    results["init_time_ms"] = init_time * 1000

    # Run ingestion
    ingest_start = time.perf_counter()
    graph, tracker, stats = ingestor.ingest()
    ingest_time = time.perf_counter() - ingest_start
    results["ingest_time_ms"] = ingest_time * 1000

    # Ingestion stats
    results["files_processed"] = stats.files_processed
    results["nodes_created"] = stats.nodes_created
    results["edges_created"] = stats.edges_created

    # Measure minified graph size (signatures only)
    minified_content = "\n".join(node.signature for node in graph.iter_nodes())
    minified_bytes = len(minified_content.encode("utf-8"))
    results["minified_bytes"] = minified_bytes
    results["minified_content"] = minified_content

    # Calculate compression ratio
    if raw_bytes > 0:
        results["compression_ratio"] = raw_bytes / max(minified_bytes, 1)
        results["space_savings_percent"] = (1 - minified_bytes / raw_bytes) * 100
    else:
        results["compression_ratio"] = 0
        results["space_savings_percent"] = 0

    # Query benchmarks (if we have nodes)
    if graph.node_count > 0:
        sample_node = next(graph.iter_nodes())
        sample_name = sample_node.name

        iterations = 100

        start = time.perf_counter()
        for _ in range(iterations):
            graph.find_definition(sample_name)
        results["find_definition_us"] = (time.perf_counter() - start) / iterations * 1_000_000

        start = time.perf_counter()
        for _ in range(iterations):
            graph.find_callers(sample_name)
        results["find_callers_us"] = (time.perf_counter() - start) / iterations * 1_000_000

        start = time.perf_counter()
        for _ in range(iterations):
            graph.get_context_subgraph(sample_name, depth=2)
        results["get_context_us"] = (time.perf_counter() - start) / iterations * 1_000_000

    return results


def print_results(results: dict) -> None:
    """Print benchmark results in a readable format."""
    print("\n" + "=" * 60)
    print("MCP CONTEXT GRAPH BENCHMARK RESULTS")
    print("=" * 60)

    print(f"\nProject: {results['project_path']}")
    print(f"Files processed: {results['files_processed']}")
    print(f"Nodes created: {results['nodes_created']}")
    print(f"Edges created: {results['edges_created']}")

    print("\n--- CONTEXT EFFICIENCY ---")
    print(f"Raw source size:     {format_bytes(results['raw_source_bytes'])}")
    print(f"Minified graph size: {format_bytes(results['minified_bytes'])}")
    print(f"Compression ratio:   {results['compression_ratio']:.1f}x")
    print(f"Space savings:       {results['space_savings_percent']:.1f}%")

    print("\n--- PERFORMANCE ---")
    print(f"Import time:         {results['import_time_ms']:.1f} ms")
    print(f"Init time:           {results['init_time_ms']:.1f} ms")
    print(f"Ingest time:         {results['ingest_time_ms']:.1f} ms")

    if "find_definition_us" in results:
        print(f"\n--- QUERY LATENCY (avg of 100 calls) ---")
        print(f"find_definition:     {results['find_definition_us']:.1f} μs")
        print(f"find_callers:        {results['find_callers_us']:.1f} μs")
        print(f"get_context(d=2):    {results['get_context_us']:.1f} μs")

    # Financial impact analysis via OpenRouter API
    print("\n--- PROJECTED FINANCIAL IMPACT (per 1,000 interactions) ---")
    print("Token counts via OpenRouter API (exact)")
    print(f"{'Model':<20} | {'Full File':<12} | {'Graph':<12} | {'Savings':<12} | {'%':<8}")
    print("-" * 75)

    for model, config in MODEL_REGISTRY.items():
        try:
            baseline_tokens = count_tokens_for_model(results["raw_content"], model)
            graph_tokens = count_tokens_for_model(results["minified_content"], model)

            cost_base = (baseline_tokens / 1_000_000) * config['input'] * 1000
            cost_graph = (graph_tokens / 1_000_000) * config['input'] * 1000
            savings = cost_base - cost_graph
            savings_pct = (savings / cost_base * 100) if cost_base > 0 else 0

            print(f"{model:<20} | ${cost_base:<10.2f} | ${cost_graph:<10.2f} | ${savings:<10.2f} | {savings_pct:.1f}%")
        except RuntimeError as e:
            print(f"{model:<20} | ERROR: {e}")

    print("\n" + "=" * 60)


def print_markdown_table(results: dict) -> None:
    """Print results as markdown table for README."""
    print("\n### Benchmark Results\n")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Files processed | {results['files_processed']} |")
    print(f"| Nodes created | {results['nodes_created']} |")
    print(f"| Raw source size | {format_bytes(results['raw_source_bytes'])} |")
    print(f"| Minified size | {format_bytes(results['minified_bytes'])} |")
    print(f"| **Compression ratio** | **{results['compression_ratio']:.1f}x** |")
    print(f"| Ingest time | {results['ingest_time_ms']:.0f} ms |")
    if "find_definition_us" in results:
        print(f"| find_definition | {results['find_definition_us']:.0f} μs |")
        print(f"| find_callers | {results['find_callers_us']:.0f} μs |")
        print(f"| get_context(depth=2) | {results['get_context_us']:.0f} μs |")

    # Cost efficiency via OpenRouter
    print("\n### Cost Efficiency (USD per 1,000 calls)\n")
    print("*Token counts via OpenRouter API (exact)*\n")
    print("| Model | Full File | Graph | Savings | % |")
    print("|-------|-----------|-------|---------|---|")

    for model, config in MODEL_REGISTRY.items():
        try:
            baseline_tokens = count_tokens_for_model(results["raw_content"], model)
            graph_tokens = count_tokens_for_model(results["minified_content"], model)

            cost_base = (baseline_tokens / 1_000_000) * config['input'] * 1000
            cost_graph = (graph_tokens / 1_000_000) * config['input'] * 1000
            savings = cost_base - cost_graph
            savings_pct = (savings / cost_base * 100) if cost_base > 0 else 0

            print(f"| {model} | ${cost_base:.2f} | ${cost_graph:.2f} | **${savings:.2f}** | {savings_pct:.1f}% |")
        except RuntimeError as e:
            print(f"| {model} | ERROR | - | - | {e} |")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MCP Context Graph benchmarks (requires OpenRouter API key)"
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to project to benchmark"
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output results as markdown table"
    )

    args = parser.parse_args()

    if not args.project_path.exists():
        print(f"Error: Project path does not exist: {args.project_path}", file=sys.stderr)
        return 1

    # Check API key
    if not get_api_key():
        print("Error: OpenRouter API key not set.", file=sys.stderr)
        print("Set OPENROUTER_API_KEY environment variable or edit", file=sys.stderr)
        print("OPENROUTER_API_KEY in benchmarks/run_benchmarks.py", file=sys.stderr)
        return 1

    results = run_benchmarks(args.project_path.resolve())

    if args.markdown:
        print_markdown_table(results)
    else:
        print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
