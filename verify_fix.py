"""Verify that agent_council.py no longer passes invalid kwargs to ask_llm."""
import ast
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def main():
    council_path = os.path.join(os.path.dirname(__file__), "agents", "agent_council.py")

    with open(council_path, "r") as f:
        source = f.read()

    tree = ast.parse(source)

    # Find all call nodes that invoke ask_llm
    bad_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name == "ask_llm":
                for kw in node.keywords:
                    if kw.arg == "timeout_override":
                        bad_calls.append(kw.lineno)

    if bad_calls:
        print(f"FAIL: 'timeout_override' keyword still found at line(s): {bad_calls}")
        sys.exit(1)

    # Also verify ask_llm signature doesn't support timeout_override
    config_path = os.path.join(os.path.dirname(__file__), "config_core.py")
    with open(config_path, "r") as f:
        config_source = f.read()
    config_tree = ast.parse(config_source)
    for node in ast.walk(config_tree):
        if isinstance(node, ast.FunctionDef) and node.name == "ask_llm":
            arg_names = [a.arg for a in node.args.args] + [a.arg for a in node.args.kwonlyargs]
            if "timeout_override" not in arg_names:
                print("PASS: ask_llm() does not accept timeout_override, and agent_council.py doesn't pass it.")
                sys.exit(0)
            break

    print("FAIL: Could not find ask_llm definition in config_core.py")
    sys.exit(1)

if __name__ == "__main__":
    main()
