import requests
import time

# Read token from file
with open('test_token.txt', 'r') as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}'}
base_url = 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1'

print('🧱 7. MULTI-TENANT ISOLATION VALIDATION')
print('=' * 50)

# Create a second test user
try:
    register_url = f'{base_url}/auth/register'
    user2_data = {
        'email': f'test2user{int(time.time())}@example.com',
        'password': 'TestPass123!',
        'firstName': 'Test2',
        'lastName': 'User',
        'acceptTerms': True,
        'acceptPrivacy': True,
        'recaptchaToken': 'test-token'
    }

    response = requests.post(register_url, json=user2_data, timeout=10)
    print(f'✅ Register second user: {response.status_code}')

    if response.status_code == 201:
        # Login with second user
        login_url = f'{base_url}/auth/login'
        login_data = {
            'email': user2_data['email'],
            'password': user2_data['password'],
            'recaptchaToken': 'test-token'
        }

        response = requests.post(login_url, json=login_data, timeout=10)
        print(f'✅ Login second user: {response.status_code}')

        if response.status_code == 200:
            token2_data = response.json()
            token2 = token2_data.get('access_token')
            headers2 = {'Authorization': f'Bearer {token2}'}

            # Try to access first user's data with second user's token (should fail)
            # First, let's see if we can get any conversions (there shouldn't be any for user 2)
            response = requests.get(f'{base_url}/conversions', headers=headers2, timeout=10)
            print(f'✅ User2 get conversions: {response.status_code}')

            if response.status_code == 200:
                conversions = response.json()
                print(f'   User2 has {len(conversions)} conversions (should be 0)')

                # If user2 has conversions, that's bad - they shouldn't see user1's data
                if len(conversions) > 0:
                    print('   ❌ MULTI-TENANT VIOLATION: User2 can see other users data!')
                else:
                    print('   ✅ Multi-tenant isolation working')

except Exception as e:
    print(f'❌ Multi-tenant test error: {e}')

print()
print('🛡️ 8. ERROR HANDLING VALIDATION')
print('=' * 50)

# Test various error conditions
test_cases = [
    ('Invalid token', {'Authorization': 'Bearer invalid_token'}, f'{base_url}/auth/me', 401),
    ('Missing auth header', {}, f'{base_url}/conversions', 401),
    ('Invalid conversion ID', headers, f'{base_url}/conversions/invalid-id', 404),
    ('Invalid schema generate', headers, f'{base_url}/schema/generate', 422),  # Missing required fields
]

for test_name, test_headers, test_url, expected_status in test_cases:
    try:
        if 'POST' in test_name:
            response = requests.post(test_url, headers=test_headers, json={}, timeout=10)
        else:
            response = requests.get(test_url, headers=test_headers, timeout=10)

        status = response.status_code
        if status == expected_status:
            print(f'✅ {test_name}: {status} (expected)')
        else:
            print(f'❌ {test_name}: {status} (expected {expected_status})')

    except Exception as e:
        print(f'❌ {test_name} error: {e}')