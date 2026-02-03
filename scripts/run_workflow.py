#!/usr/bin/env python3
"""
Workflow Studio CLI Runner
"""

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.workflow_studio_engine import WorkflowStudioEngine


def parse_inputs(input_list):
    inputs = {}
    for item in input_list:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        inputs[key] = value
    return inputs


def main():
    parser = argparse.ArgumentParser(description="Run Workflow Studio workflow")
    parser.add_argument("--workflow", required=True, help="workflow name")
    parser.add_argument("--input", action="append", default=[], help="key=value input")
    parser.add_argument("--input-file", help="JSON file with inputs")
    args = parser.parse_args()

    inputs = parse_inputs(args.input)
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            raise SystemExit(f"input file not found: {input_path}")
        with open(input_path, "r", encoding="utf-8") as file:
            inputs.update(json.load(file))

    engine = WorkflowStudioEngine()
    result = engine.run_workflow(args.workflow, inputs)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
