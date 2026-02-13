#!/usr/bin/env python3
"""Diagnostic script to check PetroChina Gas integration structure."""

import os
import sys
import json
import importlib.util

# Change to integration directory
os.chdir('/Volumes/Samsung_T5/Mubey-Work/HAOS/petrochina-gas')
sys.path.insert(0, '.')

print("=" * 60)
print("PetroChina Gas Integration Diagnostic")
print("=" * 60)

# 1. Check manifest.json
print("\n1. Checking manifest.json...")
try:
    with open('manifest.json', 'r') as f:
        manifest = json.load(f)
    domain = manifest.get('domain')
    print(f"   ✓ domain: {domain}")
    print(f"   ✓ name: {manifest.get('name')}")
    print(f"   ✓ config_flow: {manifest.get('config_flow')}")
    print(f"   ✓ icon: {manifest.get('icon', 'NOT SET')}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# 2. Calculate expected class name
print(f"\n2. Expected ConfigFlow class name...")
parts = domain.split('_')
expected_class = ''.join(p.title() for p in parts) + 'ConfigFlow'
print(f"   Expected: {expected_class}")

# 3. Check if config_flow.py exists and has the class
print(f"\n3. Checking config_flow.py...")
try:
    spec = importlib.util.spec_from_file_location("config_flow", "config_flow.py")
    config_flow_module = importlib.util.module_from_spec(spec)

    # Check if we can at least parse the file
    with open('config_flow.py', 'r') as f:
        code = f.read()
    compile(code, 'config_flow.py', 'exec')
    print(f"   ✓ config_flow.py syntax is valid")

    # Find the class definition
    import re
    class_match = re.search(r'class\s+(\w+ConfigFlow)', code)
    if class_match:
        actual_class = class_match.group(1)
        print(f"   Found class: {actual_class}")
        if actual_class == expected_class:
            print(f"   ✓ Class name matches domain!")
        else:
            print(f"   ✗ Class name MISMATCH!")
except SyntaxError as e:
    print(f"   ✗ Syntax Error: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. Check const.py
print(f"\n4. Checking const.py...")
try:
    from const import DOMAIN, CONF_UPDATE_INTERVAL
    print(f"   ✓ DOMAIN = {DOMAIN}")
    print(f"   ✓ CONF_UPDATE_INTERVAL = {CONF_UPDATE_INTERVAL}")
    if DOMAIN == domain:
        print(f"   ✓ const.DOMAIN matches manifest.domain")
    else:
        print(f"   ✗ MISMATCH: const.DOMAIN={DOMAIN} != {domain}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 5. Check gas_client
print(f"\n5. Checking gas_client...")
try:
    from gas_client import GasHttpClient, CSGAPIError
    print(f"   ✓ GasHttpClient imported")
    print(f"   ✓ CSGAPIError imported")
    # Test init without user_code
    client = GasHttpClient(cid=2)
    print(f"   ✓ GasHttpClient(cid=2) works")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 6. Check __init__.py
print(f"\n6. Checking __init__.py...")
try:
    from importlib import import_module
    main_module = import_module('__init__')
    print(f"   ✓ Main __init__.py imports successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 7. Check strings.json
print(f"\n7. Checking strings.json...")
try:
    with open('strings.json', 'r') as f:
        strings = json.load(f)
    config_steps = strings.get('config', {}).get('step', {})
    print(f"   ✓ config steps: {list(config_steps.keys())}")
    config_errors = strings.get('config', {}).get('error', {})
    print(f"   ✓ config errors: {list(config_errors.keys())}")
    config_aborts = strings.get('config', {}).get('abort', {})
    print(f"   ✓ config aborts: {list(config_aborts.keys())}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 8. Check files exist
print(f"\n8. Checking required files...")
required_files = [
    '__init__.py',
    'manifest.json',
    'config_flow.py',
    'const.py',
    'strings.json',
    'sensor.py',
    'requirements.txt',
    'gas_client/__init__.py',
    'gas_client/client.py',
    'gas_client/models.py',
    'gas_client/const.py',
]
for f in required_files:
    if os.path.exists(f):
        print(f"   ✓ {f}")
    else:
        print(f"   ✗ MISSING: {f}")

# 9. Check folder structure
print(f"\n9. Folder structure check...")
current_folder = os.path.basename(os.getcwd())
print(f"   Current folder: {current_folder}")
print(f"   Expected folder: {domain}")
if current_folder == domain:
    print(f"   ✓ Folder name matches domain!")
else:
    print(f"   ✗ WARNING: Folder name should be '{domain}'")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
