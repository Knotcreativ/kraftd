#!/usr/bin/env python3
"""
AZURE CREDENTIALS CONFIGURATION SCRIPT
=====================================

This script helps configure Azure service credentials for Kraftd deployment.
Run this to automatically retrieve and update your .env file with real Azure keys.

Note: For GitHub Actions, prefer using explicit per-field secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`) instead of the full `AZURE_CREDENTIALS` JSON to avoid parsing issues. See `docs/SECRETS_AZURE.md` for details.

Requirements:
- Azure CLI installed and logged in (az login)
- Access to the Azure subscription and resources

Usage: python configure_azure_credentials.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class AzureCredentialsConfigurator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.credentials = {}

    def run_az_command(self, command):
        """Run Azure CLI command and return JSON result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode != 0:
                print(f"Azure CLI Error: {result.stderr}")
                return None

            if result.stdout.strip():
                return json.loads(result.stdout)
            return None

        except Exception as e:
            print(f"Command execution error: {e}")
            return None

    def check_az_login(self):
        """Check if user is logged into Azure CLI"""
        print("Checking Azure CLI login status...")

        account_info = self.run_az_command("az account show")
        if not account_info:
            print("❌ Not logged into Azure CLI")
            print("Please run: az login")
            return False

        print(f"✅ Logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
        print(f"   Subscription: {account_info.get('name', 'Unknown')}")
        return True

    def get_cosmos_connection_string(self):
        """Get Cosmos DB connection string"""
        print("\n🔍 Retrieving Cosmos DB connection string...")

        # Try to find Cosmos DB account
        cosmos_accounts = self.run_az_command(
            'az cosmosdb list --query "[].{name:name, resourceGroup:resourceGroup}"'
        )

        if not cosmos_accounts:
            print("❌ No Cosmos DB accounts found")
            return None

        # Look for kraftdintel-cosmos
        target_account = None
        for account in cosmos_accounts:
            if "kraftdintel" in account.get("name", "").lower():
                target_account = account
                break

        if not target_account:
            print("❌ kraftdintel-cosmos account not found")
            print("Available accounts:", [acc.get("name") for acc in cosmos_accounts])
            return None

        account_name = target_account["name"]
        resource_group = target_account["resourceGroup"]

        print(f"Found Cosmos DB account: {account_name}")

        # Get connection strings
        conn_strings = self.run_az_command(
            f"az cosmosdb keys list --name {account_name} --resource-group {resource_group} --type connection-strings"
        )

        if conn_strings and "connectionStrings" in conn_strings:
            connection_string = conn_strings["connectionStrings"][0]["connectionString"]
            print("✅ Cosmos DB connection string retrieved")
            return connection_string

        print("❌ Failed to retrieve Cosmos DB connection string")
        return None

    def get_openai_key(self):
        """Get Azure OpenAI API key"""
        print("\n🔍 Retrieving Azure OpenAI API key...")

        # Try to find OpenAI resources
        openai_accounts = self.run_az_command(
            'az cognitiveservices account list --query "[].{name:name, resourceGroup:resourceGroup, kind:kind}"'
        )

        if not openai_accounts:
            print("❌ No Cognitive Services accounts found")
            return None

        # Look for OpenAI account
        target_account = None
        for account in openai_accounts:
            if account.get("kind") == "OpenAI" and "kraftdintel" in account.get("name", "").lower():
                target_account = account
                break

        if not target_account:
            print("❌ kraftdintel-openai account not found")
            openai_accounts_list = [acc for acc in openai_accounts if acc.get("kind") == "OpenAI"]
            if openai_accounts_list:
                print("Available OpenAI accounts:", [acc.get("name") for acc in openai_accounts_list])
            return None

        account_name = target_account["name"]
        resource_group = target_account["resourceGroup"]

        print(f"Found OpenAI account: {account_name}")

        # Get API keys
        keys = self.run_az_command(
            f"az cognitiveservices account keys list --name {account_name} --resource-group {resource_group}"
        )

        if keys and "key1" in keys:
            api_key = keys["key1"]
            print("✅ Azure OpenAI API key retrieved")
            return api_key

        print("❌ Failed to retrieve Azure OpenAI API key")
        return None

    def get_document_intelligence_key(self):
        """Get Document Intelligence API key"""
        print("\n🔍 Retrieving Document Intelligence API key...")

        # Try to find Document Intelligence resources
        docintel_accounts = self.run_az_command(
            'az cognitiveservices account list --query "[].{name:name, resourceGroup:resourceGroup, kind:kind}"'
        )

        if not docintel_accounts:
            print("❌ No Cognitive Services accounts found")
            return None

        # Look for Document Intelligence account
        target_account = None
        for account in docintel_accounts:
            if "docintel" in account.get("name", "").lower() or "documentintelligence" in account.get("name", "").lower():
                target_account = account
                break

        if not target_account:
            print("❌ Document Intelligence account not found")
            print("Available accounts:", [acc.get("name") for acc in docintel_accounts])
            return None

        account_name = target_account["name"]
        resource_group = target_account["resourceGroup"]

        print(f"Found Document Intelligence account: {account_name}")

        # Get API keys
        keys = self.run_az_command(
            f"az cognitiveservices account keys list --name {account_name} --resource-group {resource_group}"
        )

        if keys and "key1" in keys:
            api_key = keys["key1"]
            print("✅ Document Intelligence API key retrieved")
            return api_key

        print("❌ Failed to retrieve Document Intelligence API key")
        return None

    def update_env_file(self):
        """Update the .env file with retrieved credentials"""
        print("\n📝 Updating .env file...")

        if not self.env_file.exists():
            print("❌ .env file not found")
            return False

        # Read current content
        with open(self.env_file, 'r') as f:
            content = f.read()

        # Update credentials
        updates = {
            "AZURE_COSMOS_CONNECTION_STRING": self.credentials.get("cosmos"),
            "AZURE_OPENAI_KEY": self.credentials.get("openai"),
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": self.credentials.get("docintel")
        }

        for var_name, new_value in updates.items():
            if new_value:
                # Replace placeholder values
                old_pattern = f"{var_name}=YOUR_"
                new_line = f"{var_name}={new_value}"

                if old_pattern in content:
                    content = content.replace(old_pattern, new_line)
                    print(f"✅ Updated {var_name}")
                else:
                    print(f"⚠️  Could not find placeholder for {var_name}")

        # Write back to file
        with open(self.env_file, 'w') as f:
            f.write(content)

        print("✅ .env file updated successfully")
        return True

    def run_configuration(self):
        """Run the complete credential configuration process"""
        print("🔧 AZURE CREDENTIALS CONFIGURATION")
        print("=" * 50)

        # Check Azure CLI login
        if not self.check_az_login():
            return False

        # Retrieve credentials
        self.credentials["cosmos"] = self.get_cosmos_connection_string()
        self.credentials["openai"] = self.get_openai_key()
        self.credentials["docintel"] = self.get_document_intelligence_key()

        # Check if we got all credentials
        missing = []
        for key, value in self.credentials.items():
            if not value:
                missing.append(key.upper())

        if missing:
            print(f"\n❌ Missing credentials: {', '.join(missing)}")
            print("\nManual configuration required:")
            print("1. Go to Azure Portal")
            print("2. Navigate to each service")
            print("3. Copy keys from 'Keys' section")
            print("4. Update .env file manually")
            return False

        # Update .env file
        if self.update_env_file():
            print("\n🎉 SUCCESS: All Azure credentials configured!")
            print("\nReady for deployment. Run:")
            print("  ./deploy-azure.bat  # Windows")
            print("  ./deploy-azure.sh   # Linux/Mac")
            return True

        return False

if __name__ == "__main__":
    configurator = AzureCredentialsConfigurator()
    success = configurator.run_configuration()

    if not success:
        print("\n❌ Configuration failed. Please check Azure access and try again.")
        sys.exit(1)