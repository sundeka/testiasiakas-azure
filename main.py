from azure.identity import ClientSecretCredential
import requests
import os

CUSTOMER_NAME = "Testiasiakas Oyj"
CUSTOMER_TECH_NAME = "testiasiakas"
GH_ORG_NAME = "sundeka"
GH_REPO_NAME = "testiasiakas-azure"

"""
Authenticate in as Dolphin's Service Principal
"""
credentials = ClientSecretCredential(
    os.environ["TENANT_ID"],
    os.environ["DOLPHIN_SP_USER"],
    os.environ["DOLPHIN_SP_PASS"]
)
access_token = credentials.get_token("https://graph.microsoft.com/.default").token

"""
Create an app registration using Dolphin's identity

Required Dolphin SP permissions in Azure:
- Application.ReadWrite.OwnedBy
"""
url = "https://graph.microsoft.com/v1.0/applications"
headers = {"Authorization": f"Bearer {access_token}"}
payload = {
    "displayName": "testiasiakas-sp"
}
response = requests.post(url,headers=headers,json=payload)
customer_sp_oid = response.json()["id"]
customer_sp_app_id = response.json()["appId"]

"""
Create federated credentials for the customer's SP.

Required Dolphin SP permission:
- 
"""
url = f"https://graph.microsoft.com/v1.0/applications/{customer_sp_oid}/federatedIdentityCredentials"
headers = {"Authorization": f"Bearer {access_token}"}
payload = {
    "name": f"gha-pipeline-{CUSTOMER_TECH_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": f"repo:{GH_ORG_NAME}/{GH_REPO_NAME}:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"],
    "claimsMatchingExpression": None
}

response = requests.post(url,headers=headers,json=payload)