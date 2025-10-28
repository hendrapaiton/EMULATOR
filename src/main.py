import os
import requests
import argparse
from dotenv import load_dotenv
import json
from fhir.resources.patient import Patient
from fhir.resources.identifier import Identifier
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept

def filter_response(data, keys_to_remove):
    """
    Recursively filter out specified keys from the response data.
    """
    if isinstance(data, dict):
        return {k: filter_response(v, keys_to_remove) for k, v in data.items() if k not in keys_to_remove}
    elif isinstance(data, list):
        return [filter_response(item, keys_to_remove) for item in data]
    else:
        return data

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

def get_patient(nik, access_token, base_url='https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1'):
    """
    Retrieve patient data from SatuSehat API using NIK and parse into FHIR Patient resource.

    Args:
        nik (str): National Identity Number (NIK) of the patient.
        access_token (str): Bearer token for API authentication.
        base_url (str): Base URL for the SatuSehat FHIR API.

    Returns:
        Patient: FHIR Patient resource object.

    Raises:
        ValueError: If access_token is not provided.
        Exception: If API request fails or parsing encounters an error.
    """
    if not access_token:
        raise ValueError("Access token must be provided")

    # Use the correct FHIR identifier system for NIK in SatuSehat
    patient_url = f"{base_url}/Patient?identifier=https://fhir.kemkes.go.id/id/nik|{nik}"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(patient_url, headers=headers)

    if response.status_code == 200:
        patient_data = response.json()
        # Parse the JSON response into a FHIR Patient resource
        try:
            patient_resource = Patient(**patient_data['entry'][0]['resource'])
            return patient_resource
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse patient data: {e}")
    else:
        raise Exception(f"Failed to retrieve patient data: {response.status_code} - {response.text}")

def get_practitioner(nik, access_token, base_url='https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1'):
    """
    Retrieve practitioner data from SatuSehat API using NIK.
    """
    if not access_token:
        raise ValueError("Access token must be provided")

    # Use the correct FHIR identifier system for NIK in SatuSehat
    practitioner_url = f"{base_url}/Practitioner?identifier=https://fhir.kemkes.go.id/id/nik|{nik}"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(practitioner_url, headers=headers)

    if response.status_code == 200:
        practitioner_data = response.json()
        return practitioner_data
    else:
        raise Exception(f"Failed to retrieve practitioner data: {response.status_code} - {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage access token and patient data from SatuSehat API')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Token subcommand
    token_parser = subparsers.add_parser('token', help='Manage access token')
    token_parser.add_argument('action', choices=['get', 'update'], help='Action to perform: get (retrieve from file) or update (fetch new token)')
    token_parser.add_argument('--client-id', help='Client ID for SatuSehat API', default=os.getenv('SATUSEHAT_CLIENT_ID'))
    token_parser.add_argument('--client-secret', help='Client Secret for SatuSehat API', default=os.getenv('SATUSEHAT_CLIENT_SECRET'))
    token_parser.add_argument('--base-url', help='Base URL for SatuSehat API', default='https://api-satusehat-stg.dto.kemkes.go.id')

    # Patient subcommand
    patient_parser = subparsers.add_parser('patient', help='Retrieve patient data by NIK')
    patient_parser.add_argument('--nik', required=True, help='NIK (National Identity Number) of the patient')

    # Practitioner subcommand
    practitioner_parser = subparsers.add_parser('practitioner', help='Retrieve practitioner data by NIK')
    practitioner_parser.add_argument('--nik', required=True, help='NIK (National Identity Number) of the practitioner')

    args = parser.parse_args()

    if args.command == 'token':
        if args.action == 'get':
            try:
                with open('access_token.txt', 'r') as f:
                    token = f.read().strip()
                print(f"Access token: {token}")
            except FileNotFoundError:
                print("Error: access_token.txt not found. Use 'token update' to fetch a new token.")
            except Exception as e:
                print(f"Error reading token: {e}")
        elif args.action == 'update':
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
    elif args.command == 'patient':
        try:
            with open('access_token.txt', 'r') as f:
                access_token = f.read().strip()
        except FileNotFoundError:
            print("Error: access_token.txt not found. Use 'token update' to fetch a new token first.")
            exit(1)
        except Exception as e:
            print(f"Error reading token: {e}")
            exit(1)

        try:
            patient_resource = get_patient(args.nik, access_token)
            # Convert the FHIR Patient resource back to dict for filtering and printing
            patient_dict = patient_resource.model_dump()
            filtered_data = filter_response(patient_dict, ['other', 'link'])
            print(json.dumps(filtered_data, indent=2, default=str))
        except Exception as e:
            print(f"Error retrieving patient data: {e}")
            if "401" in str(e):
                print("Token may be expired. Use 'token update' to refresh the token.")
    elif args.command == 'practitioner':
        try:
            with open('access_token.txt', 'r') as f:
                access_token = f.read().strip()
        except FileNotFoundError:
            print("Error: access_token.txt not found. Use 'token update' to fetch a new token first.")
            exit(1)
        except Exception as e:
            print(f"Error reading token: {e}")
            exit(1)

        try:
            practitioner_data = get_practitioner(args.nik, access_token)
            # Recursively filter out 'other' and 'link' fields from the response
            filtered_data = filter_response(practitioner_data, ['other', 'link'])
            print(json.dumps(filtered_data, indent=2))
        except Exception as e:
            print(f"Error retrieving practitioner data: {e}")
            if "401" in str(e):
                print("Token may be expired. Use 'token update' to refresh the token.")
