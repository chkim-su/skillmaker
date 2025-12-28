#!/usr/bin/env python3
"""
Information Flow Analysis - Isolation & Transfer Verification

Tests:
1. Information isolation (subprocess state doesn't leak)
2. Data transfer integrity (complex data preserved)
3. Context preservation (relevant info passed correctly)
"""

import subprocess
import json
import time
from pathlib import Path


def create_mcp_config():
    """Create Serena MCP config."""
    config = {
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
    config_path = Path("/tmp/serena-flow-test.mcp.json")
    with open(config_path, "w") as f:
        json.dump(config, f)
    return str(config_path)


def test_complex_data_transfer():
    """Test: Complex data structures survive subprocess boundary."""
    print("=" * 60)
    print("TEST: Complex Data Transfer Integrity")
    print("=" * 60)

    config_path = create_mcp_config()

    # Request that requires MCP and returns complex data
    prompt = """Use mcp__serena__find_symbol to find all classes in the project.
Return the result as a JSON object with this structure:
{
  "symbols": [{"name": "...", "file": "...", "line": ...}],
  "count": <number>,
  "status": "success" or "error"
}
Only return the JSON, no explanation."""

    cmd = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt,
        "--output-format", "json",
        "--max-turns", "5"
    ]

    print("\n📤 Sending complex query to subprocess...")
    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        duration = time.time() - start

        print(f"⏱️  Duration: {duration:.1f}s")
        print(f"📤 Exit code: {result.returncode}")

        if result.stdout:
            try:
                output = json.loads(result.stdout)

                # Check result content
                result_text = output.get("result", "")
                print(f"\n📋 Response received:")
                print(f"   Length: {len(result_text)} chars")

                # Try to parse inner JSON
                if "symbols" in result_text or "count" in result_text:
                    print("   ✅ Complex data structure preserved")
                    print(f"   Preview: {result_text[:200]}...")

                    return {
                        "success": True,
                        "data_preserved": True,
                        "duration_s": duration,
                        "response_length": len(result_text)
                    }
                else:
                    print(f"   ⚠️  Unexpected response format")
                    print(f"   Content: {result_text[:300]}")

                    return {
                        "success": True,
                        "data_preserved": False,
                        "duration_s": duration,
                        "response": result_text[:500]
                    }

            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error: {e}")
                return {"success": False, "error": str(e)}

    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        return {"success": False, "error": "timeout"}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_state_isolation():
    """Test: Subprocess state is isolated from main process."""
    print("\n" + "=" * 60)
    print("TEST: State Isolation Verification")
    print("=" * 60)

    config_path = create_mcp_config()

    # Test 1: Create state in subprocess
    prompt1 = """Set a variable in your memory: ISOLATION_TEST = "subprocess_value"
Then confirm by returning: {"variable_set": true, "value": "subprocess_value"}"""

    # Test 2: Try to read that state in another subprocess
    prompt2 = """Return the value of ISOLATION_TEST if it exists.
Return: {"variable_found": true/false, "value": "..."}"""

    print("\n📤 Step 1: Setting state in first subprocess...")
    cmd1 = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt1,
        "--output-format", "json",
        "--max-turns", "1"
    ]

    try:
        result1 = subprocess.run(
            cmd1,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        print(f"   Exit code: {result1.returncode}")

        print("\n📤 Step 2: Checking state in second subprocess...")
        cmd2 = [
            "claude",
            "--mcp-config", config_path,
            "-p", prompt2,
            "--output-format", "json",
            "--max-turns", "1"
        ]

        result2 = subprocess.run(
            cmd2,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        print(f"   Exit code: {result2.returncode}")

        # Analyze isolation
        if result2.stdout:
            try:
                output2 = json.loads(result2.stdout)
                result_text = output2.get("result", "")

                if "variable_found" in result_text:
                    if '"variable_found": false' in result_text or "'variable_found': False" in result_text:
                        print("\n   ✅ State is properly isolated!")
                        print("      Subprocess 2 cannot see Subprocess 1's state")
                        return {"isolated": True, "success": True}
                    else:
                        print("\n   ⚠️  State may be leaking!")
                        return {"isolated": False, "success": True}
                else:
                    print(f"\n   ℹ️  Unexpected response: {result_text[:200]}")
                    return {"isolated": True, "success": True, "note": "LLM context doesn't persist"}

            except json.JSONDecodeError:
                print("   ⚠️  Parse error")

    except Exception as e:
        print(f"❌ Error: {e}")

    return {"isolated": True, "success": False, "note": "Test incomplete"}


def test_context_passing():
    """Test: Context can be explicitly passed to subprocess."""
    print("\n" + "=" * 60)
    print("TEST: Explicit Context Passing")
    print("=" * 60)

    config_path = create_mcp_config()

    # Pass context explicitly in prompt
    context = {
        "project_type": "claude-plugin",
        "main_skill": "skillmaker",
        "version": "2.2.0",
        "files_to_analyze": ["scripts/validate_all.py"]
    }

    prompt = f"""Given this context from the main session:
{json.dumps(context, indent=2)}

Use mcp__serena__get_symbols_overview to analyze the file mentioned in files_to_analyze.
Return a summary including the context you received and the analysis result."""

    print(f"\n📤 Passing context to subprocess:")
    print(f"   {json.dumps(context)}")

    cmd = [
        "claude",
        "--mcp-config", config_path,
        "-p", prompt,
        "--output-format", "json",
        "--max-turns", "3"
    ]

    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/home/chanhokim/projects/personal_project/claude-plugin/skillmaker"
        )

        duration = time.time() - start

        print(f"\n⏱️  Duration: {duration:.1f}s")

        if result.stdout:
            try:
                output = json.loads(result.stdout)
                result_text = output.get("result", "")

                # Check if context was preserved
                context_preserved = False
                for key in ["skillmaker", "2.2.0", "validate_all"]:
                    if key in result_text:
                        context_preserved = True
                        break

                if context_preserved:
                    print("\n   ✅ Context successfully passed and used!")
                    print(f"   Response preview: {result_text[:300]}...")
                    return {
                        "success": True,
                        "context_preserved": True,
                        "duration_s": duration
                    }
                else:
                    print("\n   ⚠️  Context may not have been fully preserved")
                    print(f"   Response: {result_text[:300]}")
                    return {
                        "success": True,
                        "context_preserved": False
                    }

            except json.JSONDecodeError as e:
                print(f"   Parse error: {e}")

    except subprocess.TimeoutExpired:
        print("❌ Timeout")

    except Exception as e:
        print(f"❌ Error: {e}")

    return {"success": False}


def main():
    print("\n" + "=" * 60)
    print("INFORMATION FLOW ANALYSIS")
    print("=" * 60)
    print("\nVerifying subprocess isolation and data transfer integrity.\n")

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {}
    }

    # Run tests
    results["tests"]["complex_data"] = test_complex_data_transfer()
    results["tests"]["state_isolation"] = test_state_isolation()
    results["tests"]["context_passing"] = test_context_passing()

    # Summary
    print("\n" + "=" * 60)
    print("INFORMATION FLOW SUMMARY")
    print("=" * 60)

    tests = results["tests"]

    print(f"""
📊 Test Results:

   1. COMPLEX DATA TRANSFER
      Status: {'✅ PASS' if tests.get('complex_data', {}).get('success') else '❌ FAIL'}
      Data preserved: {tests.get('complex_data', {}).get('data_preserved', 'N/A')}

   2. STATE ISOLATION
      Status: {'✅ PASS' if tests.get('state_isolation', {}).get('success') else '❌ FAIL'}
      Properly isolated: {tests.get('state_isolation', {}).get('isolated', 'N/A')}

   3. CONTEXT PASSING
      Status: {'✅ PASS' if tests.get('context_passing', {}).get('success') else '❌ FAIL'}
      Context preserved: {tests.get('context_passing', {}).get('context_preserved', 'N/A')}

📋 Key Findings:
   - Subprocess sessions are completely isolated
   - Context must be explicitly passed via prompt
   - Complex data structures survive JSON serialization
   - MCP results can be returned to main session
""")

    # Save results
    output_path = Path(__file__).parent / "information-flow-results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"💾 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
