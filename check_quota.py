import requests

# Read token from file
with open('test_token.txt', 'r') as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}'}
base_url = 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1'

print('🔍 4. QUOTA ENFORCEMENT VALIDATION')
print('=' * 50)

# Check quota status
try:
    response = requests.get(f'{base_url}/quota', headers=headers, timeout=10)
    print(f'✅ Get quota: {response.status_code}')

    if response.status_code == 200:
        quota = response.json()
        print(f'   Conversions used: {quota.get("conversions_used", "N/A")}')
        print(f'   API calls used: {quota.get("api_calls_used", "N/A")}')
        print(f'   Exports used: {quota.get("exports_used", "N/A")}')
        print(f'   Conversions limit: {quota.get("conversions_limit", "N/A")}')
        print(f'   API calls limit: {quota.get("api_calls_limit", "N/A")}')
        print(f'   Exports limit: {quota.get("exports_limit", "N/A")}')
    else:
        print(f'   ❌ Quota check failed: {response.text}')

except Exception as e:
    print(f'❌ Quota check error: {e}')

print()
print('🔄 3. END-TO-END WORKFLOW VALIDATION (SIMPLE)')
print('=' * 50)

# Try a simple conversion creation to see the exact error
try:
    conversion_data = {
        'document_name': 'Test Document.pdf',
        'file_path': '/test/path.pdf',
        'document_content': 'This is test document content for validation.'
    }
    response = requests.post(f'{base_url}/conversions',
                           json=conversion_data, headers=headers, timeout=10)
    print(f'✅ Create conversion: {response.status_code}')

    if response.status_code == 500:
        print(f'   Error details: {response.text}')
    elif response.status_code == 201:
        print('   ✅ Conversion created successfully!')
    else:
        print(f'   Response: {response.text}')

except Exception as e:
    print(f'❌ Conversion creation error: {e}')