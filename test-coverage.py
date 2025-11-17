import json

# 1. Load dbt artifacts
with open('target/manifest.json') as f:
    manifest = json.load(f)
with open('target/run_results.json') as f:
    run_results = json.load(f)

# 2. Build reverse mapping: model -> tests by examining all test nodes
model_tests = {}
for node_id, node in manifest['nodes'].items():
    if node['resource_type'] == 'model':
        model_name = node['name']
        model_tests[model_name] = []

# Find all tests and map them to their models
for node_id, node in manifest['nodes'].items():
    if node['resource_type'] == 'test':
        # Tests depend on models through depends_on.nodes
        depends_on = node.get('depends_on', {}).get('nodes', [])
        for dep in depends_on:
            if dep in manifest['nodes'] and manifest['nodes'][dep]['resource_type'] == 'model':
                model_name = manifest['nodes'][dep]['name']
                if model_name in model_tests:
                    model_tests[model_name].append(node_id)

# 3. Get test execution details from run_results
test_results = {result['unique_id']: result for result in run_results['results'] if result['unique_id'].startswith('test.') or result['unique_id'].startswith('data_tests.')}

# 4. Print/validate models without tests or failed tests
passed_tests = []
failed_tests = []

for model, tests in model_tests.items():
    if not tests:
        print(f'Model "{model}" has NO tests.')
    for test_id in tests:
        result = test_results.get(test_id)
        if result:
            if result['status'] == 'pass':
                passed_tests.append((model, test_id, result['status']))
            elif result['status'] != 'pass':
                failed_tests.append((model, test_id, result['status']))

# Print summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"\nTotal Tests: {len(passed_tests) + len(failed_tests)}")
print(f"✓ Passed: {len(passed_tests)}")
print(f"✗ Failed: {len(failed_tests)}")

if passed_tests:
    print("\n--- PASSED TESTS ---")
    for model, test_id, status in passed_tests:
        test_name = test_id.split('.')[-2]
        print(f"  ✓ {test_name} ({model})")

if failed_tests:
    print("\n--- FAILED TESTS ---")
    for model, test_id, status in failed_tests:
        test_name = test_id.split('.')[-2]
        print(f"  ✗ {test_name} ({model})")

print("\n" + "="*80)

# 5. Optionally: fail script/CI if untested models or failed tests found
untested_models = [model for model, tests in model_tests.items() if not tests]

if untested_models or failed_tests:
    print("\n⚠️  SCRIPT FAILED - Issues detected:")
    if untested_models:
        print(f"\n  • Untested Models ({len(untested_models)}):")
        for model in untested_models:
            print(f"    - {model}")
    if failed_tests:
        print(f"\n  • Failed Tests ({len(failed_tests)}):")
        for model, test_id, status in failed_tests:
            test_name = test_id.split('.')[-2]
            print(f"    - {test_name} ({model})")
    print("\nExiting with error code 1")
    exit(1)
else:
    print("\n✓ SUCCESS - All models are tested and all tests passed!")
    print("Exiting with success code 0")
    exit(0)
