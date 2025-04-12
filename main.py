"""
Required Dolphin SP permissions in Azure:
- Application.ReadWrite.OwnedBy

Needs the following privileged role:
- Role Based Access Control Administrator 
    id: f58310d9-a9f6-439a-9e8d-f62e7b41a168
    selection: "Allow user to only assign selected roles to selected principals (fewer privileges)"
    constraint: "Allow user to only assign roles you select" --> Privileged -> Contributor
"""

from azure.identity import ClientSecretCredential
import requests
import os
import uuid

CUSTOMER_NAME = "Testiasiakas Oyj"
CUSTOMER_TECH_NAME = "testiasiakas"
GH_ORG_NAME = "sundeka"
GH_REPO_NAME = "testiasiakas-azure"



# 1. Authenticate in as Dolphin's Service Principal
credentials = ClientSecretCredential(
    os.environ["TENANT_ID"],
    os.environ["DOLPHIN_SP_USER"],
    os.environ["DOLPHIN_SP_PASS"]
)
graph_token = credentials.get_token("https://graph.microsoft.com/.default").token
mgmt_token = credentials.get_token("https://management.azure.com/.default").token



# 2. Create Terraform state storage resources
# NOTE: This code already exists in Dolphin. Not rewriting logic here.



# 3. Create an app registration using Dolphin's identity
url = "https://graph.microsoft.com/v1.0/applications"
headers = {"Authorization": f"Bearer {graph_token}"}
payload = {
    "displayName": "testiasiakas-sp"
}
response = requests.post(url,headers=headers,json=payload)
customer_app_oid = response.json()["id"]
customer_app_id = response.json()["appId"]



# 4. Create a service principal for the app registration
url = "https://graph.microsoft.com/v1.0/servicePrincipals"
headers = {"Authorization": f"Bearer {graph_token}"}
payload = {
    "appId": customer_app_id
}
response = requests.post(url,headers=headers,json=payload)
service_principal_oid = response.json()["id"]



# 5. Create federated credentials for the customer's app registration.
url = f"https://graph.microsoft.com/v1.0/applications/{customer_app_oid}/federatedIdentityCredentials"
headers = {"Authorization": f"Bearer {graph_token}"}
payload = {
    "name": f"gha-pipeline-{CUSTOMER_TECH_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": f"repo:{GH_ORG_NAME}/{GH_REPO_NAME}:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"],
    "claimsMatchingExpression": None
}
response = requests.post(url,headers=headers,json=payload)



# 6. Grant "Contributor" access on subscription level for customer's service principal
role_assignment_id = str(uuid.uuid4())
url = f"https://management.azure.com/subscriptions/{os.environ["SUBSCRIPTION_ID"]}/providers/Microsoft.Authorization/roleAssignments/{role_assignment_id}?api-version=2022-04-01"
headers = {"Authorization": f"Bearer {mgmt_token}"}
payload = {
  "properties": {
    "roleDefinitionId": f"/subscriptions/{os.environ["SUBSCRIPTION_ID"]}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c", 
    "principalId": service_principal_oid
  }
}
response = requests.put(url,headers=headers,json=payload)