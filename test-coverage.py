# Script: test-coverage.py
# Description: This script analyzes dbt artifacts (manifest.json and run_results.json)
import json
import sys

# 1. Load dbt artifacts
with open('target/manifest.json') as f:
    manifest = json.load(f)
try:
    with open('target/run_results.json') as f:
        run_results = json.load(f)
except FileNotFoundError:
    print("WARNING: target/run_results.json not found — proceeding without executed test results.")
    run_results = {"results": []}

# 2. Build mapping: model -> tests by examining all test nodes in manifest
model_tests = {}
for node_id, node in manifest.get('nodes', {}).items():
    if node.get('resource_type') == 'model':
        model_name = node.get('name')
        model_tests[model_name] = []

# Map each test node back to the model(s) it depends on
for node_id, node in manifest.get('nodes', {}).items():
    if node.get('resource_type') == 'test':
        depends_on = node.get('depends_on', {}).get('nodes', [])
        for dep in depends_on:
            dep_node = manifest.get('nodes', {}).get(dep)
            if dep_node and dep_node.get('resource_type') == 'model':
                model_name = dep_node.get('name')
                if model_name in model_tests:
                    model_tests[model_name].append(node_id)

# 3. Index run_results by unique_id for lookup
run_results_map = {r.get('unique_id'): r for r in run_results.get('results', [])}

# 4. Analyze test coverage and execution
passed_tests = []
failed_tests = []
not_executed_tests = []
untested_models = []

for model, tests in model_tests.items():
    if not tests:
        untested_models.append(model)
    for test_id in tests:
        result = run_results_map.get(test_id)
        if result is None:
            not_executed_tests.append((model, test_id))
        else:
            status = (result.get('status') or '').lower()
            # dbt may emit different truthy status strings depending on adapter/version
            pass_statuses = {"pass", "success", "ok"}
            if status in pass_statuses:
                passed_tests.append((model, test_id, status))
            else:
                failed_tests.append((model, test_id, status))

# 5. Print a clear summary
print("\n" + "="*80)
print("TEST COVERAGE REPORT")
print("="*80)
total_defined_tests = sum(len(t) for t in model_tests.values())
executed_tests = len(passed_tests) + len(failed_tests)
print(f"\nDefined tests: {total_defined_tests}")
print(f"Executed tests: {executed_tests}")
print(f"  ✓ Passed: {len(passed_tests)}")
print(f"  ✗ Failed: {len(failed_tests)}")
print(f"  • Not executed: {len(not_executed_tests)}")
print(f"Untested models (no tests defined): {len(untested_models)}")

if untested_models:
    print("\n--- UNTESTED MODELS ---")
    for m in untested_models:
        print(f"  - {m}")

if not_executed_tests:
    print("\n--- TESTS DEFINED BUT NOT EXECUTED ---")
    for model, test_id in not_executed_tests:
        print(f"  - {test_id} ({model})")

if passed_tests:
    print("\n--- PASSED TESTS ---")
    for model, test_id, status in passed_tests:
        test_name = test_id.split('.')[-2] if '.' in test_id else test_id
        print(f"  ✓ {test_name} ({model})")

if failed_tests:
    print("\n--- FAILED TESTS ---")
    for model, test_id, status in failed_tests:
        test_name = test_id.split('.')[-2] if '.' in test_id else test_id
        print(f"  ✗ {test_name} ({model}) - status: {status}")

print("\n" + "="*80)

# 6. Enforce CI exit codes
# Prioritize untested models as a CI-breaking reason per user request.
if untested_models:
    print("\nSCRIPT FAILED - Untested models detected.")
    print("  • Add tests for the listed models (schema.yml -> data_tests or generic tests).")
    sys.exit(2)  # distinct exit code for untested models

if failed_tests:
    print("\nSCRIPT FAILED - Failing tests detected.")
    print("  • Fix failing tests or adjust test expectations.")
    sys.exit(1)

if not_executed_tests:
    print("\nSCRIPT FAILED - Some tests were defined but not executed.")
    print("  • Ensure 'dbt test' or 'dbt build' ran and run_results.json corresponds to that run.")
    sys.exit(3)

print("\n✓ SUCCESS - All defined tests executed and passed for tested models.")
sys.exit(0)
