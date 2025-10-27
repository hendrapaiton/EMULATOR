import os
import requests
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_access_token(client_id, client_secret, base_url='https://api-satusehat-stg.dto.kemkes.go.id'):
    """
    Obtain an access token from SatuSehat using OAuth2 client credentials flow.
    """
    if not client_id or not client_secret:
        raise ValueError("client_id and client_secret must be provided")

    token_url = f"{base_url}/oauth2/v1/accesstoken?grant_type=client_credentials"

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        return token_data
    else:
        raise Exception(f"Failed to obtain access token: {response.status_code} - {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage access token from SatuSehat API')
    parser.add_argument('--token', choices=['get', 'update'], required=True, help='Action to perform: get (retrieve from file) or update (fetch new token)')
    parser.add_argument('--client-id', help='Client ID for SatuSehat API', default=os.getenv('SATUSEHAT_CLIENT_ID'))
    parser.add_argument('--client-secret', help='Client Secret for SatuSehat API', default=os.getenv('SATUSEHAT_CLIENT_SECRET'))
    parser.add_argument('--base-url', help='Base URL for SatuSehat API', default=os.getenv('SATUSEHAT_BASE_URL', 'https://api-satusehat-stg.dto.kemkes.go.id'))

    args = parser.parse_args()

    if args.token == 'get':
        try:
            with open('access_token.txt', 'r') as f:
                token = f.read().strip()
            print(f"Access token: {token}")
        except FileNotFoundError:
            print("Error: access_token.txt not found. Use --token update to fetch a new token.")
        except Exception as e:
            print(f"Error reading token: {e}")
    elif args.token == 'update':
        if not args.client_id or not args.client_secret:
            print("Error: --client-id and --client-secret are required for updating the token.")
            exit(1)
        try:
            token_data = get_access_token(args.client_id, args.client_secret, args.base_url)
            print(f"Access token obtained: {token_data}")
            # Save access_token to file
            with open('access_token.txt', 'w') as f:
                f.write(token_data['access_token'])
            print("Access token saved to access_token.txt")
        except Exception as e:
            print(f"Error: {e}")
