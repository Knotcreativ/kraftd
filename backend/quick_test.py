#!/usr/bin/env python3
import requests

try:
    r = requests.get('http://127.0.0.1:8000/health', timeout=3)
    print(f'[OK] Health: {r.status_code}')
except Exception as e:
    print(f'[FAIL] Health check failed: {e}')
    exit(1)

print()
print('Testing /auth/register...')
payload = {'email': 'test@test.com', 'name': 'Test', 'organization': 'Org', 'password': 'Pass123'}
r = requests.post('http://127.0.0.1:8000/auth/register', json=payload, timeout=5)
print(f'Status: {r.status_code}')
if r.status_code != 201:
    print(f'ERROR: {r.text}')
else:
    print(f'SUCCESS!')
    data = r.json()
    token = data.get('access_token', 'N/A')
    print(f'Access token: {token[:50]}...')
