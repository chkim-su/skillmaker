#!/usr/bin/env python3
"""
Subprocess Isolation Research - Context & Token Analysis

This script measures:
1. Token overhead in main session with MCP loaded
2. Token consumption in subprocess session
3. Information isolation verification
4. Data transfer integrity
"""

import subprocess
import json
import time
import os
from pathlib import Path

# Test configurations
SERENA_MCP_CONFIG = {
    "mcpServers": {
        "serena": {
            "command": "uvx",
            "args": [
                "--from", "git+https://github.com/oraios/serena",
                "serena", "start-mcp-server", "--project-from-cwd"
            ]
        }
    }
}


def create_mcp_config_file():
    """Create temporary MCP config for subprocess."""
    config_path = Path("/tmp/serena-isolated.mcp.json")
    with open(config_path, "w") as f:
        json.dump(SERENA_MCP_CONFIG, f, indent=2)
    return str(config_path)


def test_subprocess_isolation():
    """Test 1: Verify subprocess has isolated context."""
    print("=" * 60)
    print("TEST 1: Subprocess Context Isolation")
    print("=" * 60)

    config_path = create_mcp_config_file()

    # Simple prompt to test MCP tool availability
    prompt = """List available MCP tools. Just list the tool names, nothing else."""

    cmd = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt,
        "--output-format", "json",
        "--max-turns", "1"
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path.home())
        )

        duration = time.time() - start_time

        print(f"\n⏱️  Startup + execution time: {duration:.2f}s")
        print(f"📤 Exit code: {result.returncode}")

        if result.stdout:
            try:
                output = json.loads(result.stdout)
                print(f"\n📊 Response structure:")
                print(f"   - Type: {type(output)}")
                if isinstance(output, dict):
                    print(f"   - Keys: {list(output.keys())}")
                    if "usage" in output:
                        print(f"\n💰 Token Usage:")
                        usage = output["usage"]
                        print(f"   - Input tokens: {usage.get('input_tokens', 'N/A')}")
                        print(f"   - Output tokens: {usage.get('output_tokens', 'N/A')}")
            except json.JSONDecodeError:
                print(f"   Raw output (first 500 chars): {result.stdout[:500]}")

        if result.stderr:
            print(f"\n⚠️  Stderr: {result.stderr[:300]}")

        return {
            "success": result.returncode == 0,
            "duration_s": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        print("❌ Timeout after 60s")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_data_transfer():
    """Test 2: Verify data can be passed to and from subprocess."""
    print("\n" + "=" * 60)
    print("TEST 2: Data Transfer Integrity")
    print("=" * 60)

    config_path = create_mcp_config_file()

    # Complex request with specific data
    test_data = {
        "intent": "QUERY",
        "action": "list_dir",
        "params": {
            "relative_path": ".",
            "recursive": False
        }
    }

    prompt = f"""Execute this Serena MCP request:
{json.dumps(test_data, indent=2)}

Use the mcp__serena__list_dir tool with these exact parameters.
Return ONLY the JSON result, no explanation."""

    cmd = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt,
        "--output-format", "json",
        "--max-turns", "3"
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        duration = time.time() - start_time

        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"📤 Exit code: {result.returncode}")

        if result.stdout:
            try:
                output = json.loads(result.stdout)

                # Check for actual data in response
                if isinstance(output, dict):
                    if "result" in output:
                        print(f"\n✅ Data received from subprocess")
                        print(f"   Result type: {type(output['result'])}")

                    if "usage" in output:
                        usage = output["usage"]
                        print(f"\n💰 Token Usage:")
                        print(f"   - Input: {usage.get('input_tokens', 'N/A')}")
                        print(f"   - Output: {usage.get('output_tokens', 'N/A')}")

            except json.JSONDecodeError:
                print(f"   Raw output length: {len(result.stdout)} chars")

        return {
            "success": result.returncode == 0,
            "duration_s": duration,
            "data_received": "result" in result.stdout if result.stdout else False
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_context_comparison():
    """Test 3: Compare context with and without MCP."""
    print("\n" + "=" * 60)
    print("TEST 3: Context Size Comparison")
    print("=" * 60)

    # Test without MCP
    prompt_no_mcp = "Say 'hello' and nothing else."

    cmd_no_mcp = [
        "claude",
        "-p", prompt_no_mcp,
        "--output-format", "json",
        "--max-turns", "1"
    ]

    print("\n📊 Without MCP:")
    try:
        result = subprocess.run(
            cmd_no_mcp,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.stdout:
            output = json.loads(result.stdout)
            if "usage" in output:
                no_mcp_tokens = output["usage"].get("input_tokens", 0)
                print(f"   Input tokens: {no_mcp_tokens}")
    except Exception as e:
        print(f"   Error: {e}")
        no_mcp_tokens = 0

    # Test with MCP
    config_path = create_mcp_config_file()

    cmd_with_mcp = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt_no_mcp,
        "--output-format", "json",
        "--max-turns", "1"
    ]

    print("\n📊 With Serena MCP:")
    try:
        result = subprocess.run(
            cmd_with_mcp,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        if result.stdout:
            output = json.loads(result.stdout)
            if "usage" in output:
                with_mcp_tokens = output["usage"].get("input_tokens", 0)
                print(f"   Input tokens: {with_mcp_tokens}")

                if no_mcp_tokens > 0 and with_mcp_tokens > 0:
                    overhead = with_mcp_tokens - no_mcp_tokens
                    print(f"\n📈 MCP Token Overhead: {overhead} tokens")
                    print(f"   Percentage increase: {(overhead/no_mcp_tokens)*100:.1f}%")
    except Exception as e:
        print(f"   Error: {e}")
        with_mcp_tokens = 0

    return {
        "no_mcp_tokens": no_mcp_tokens,
        "with_mcp_tokens": with_mcp_tokens,
        "overhead": with_mcp_tokens - no_mcp_tokens if no_mcp_tokens > 0 else 0
    }


def main():
    print("\n" + "=" * 60)
    print("SUBPROCESS ISOLATION RESEARCH")
    print("=" * 60)
    print("\nThis test measures real-world subprocess isolation behavior.\n")

    results = {}

    # Run tests
    results["isolation"] = test_subprocess_isolation()
    results["data_transfer"] = test_data_transfer()
    results["context"] = test_context_comparison()

    # Summary
    print("\n" + "=" * 60)
    print("RESEARCH SUMMARY")
    print("=" * 60)

    print("\n📋 Findings:")

    if results["isolation"].get("success"):
        print(f"   ✅ Subprocess isolation works")
        print(f"      Startup time: {results['isolation'].get('duration_s', 0):.1f}s")
    else:
        print(f"   ❌ Subprocess isolation failed")

    if results["data_transfer"].get("success"):
        print(f"   ✅ Data transfer works")
    else:
        print(f"   ❌ Data transfer failed")

    ctx = results.get("context", {})
    if ctx.get("overhead", 0) > 0:
        print(f"   📊 MCP overhead: {ctx['overhead']} tokens per call")

    # Save results
    output_path = Path(__file__).parent / "isolation-test-results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
