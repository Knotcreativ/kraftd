import requests
import time

# Test the current API URL from the E2E test
url = 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1/health'
print(f'Testing API URL: {url}')

try:
    response = requests.get(url, timeout=10)
    print(f'✅ Health check: {response.status_code}')

    # Try to register a user
    register_url = 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1/auth/register'
    user_data = {
        'email': f'test{int(time.time())}@example.com',
        'password': 'TestPass123!',
        'firstName': 'Test',
        'lastName': 'User',
        'acceptTerms': True,
        'acceptPrivacy': True,
        'recaptchaToken': 'test-token'
    }

    print(f'Registering test user: {user_data["email"]}')
    response = requests.post(register_url, json=user_data, timeout=10)
    print(f'✅ Registration: {response.status_code}')

    if response.status_code == 201:
        print('✅ User created successfully!')

        # Try to login
        login_url = 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1/auth/login'
        login_data = {
            'email': user_data['email'],
            'password': user_data['password'],
            'recaptchaToken': 'test-token'
        }

        response = requests.post(login_url, json=login_data, timeout=10)
        print(f'✅ Login: {response.status_code}')

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f'✅ JWT Token obtained: {access_token[:30]}...')

            # Save token for E2E tests
            with open('test_token.txt', 'w') as f:
                f.write(access_token)
            print('✅ Token saved to test_token.txt')

        else:
            print(f'❌ Login failed: {response.text}')
    else:
        print(f'❌ Registration failed: {response.text}')

except Exception as e:
    print(f'❌ Error: {e}')