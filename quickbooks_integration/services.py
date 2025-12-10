import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class QuickBooksService:
    AUTH_BASE = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company"
    # def __init__(self, connection=None):
    #     self.connection = connection
    #     self.base_url = f"https://quickbooks.api.intuit.com/v3/company/{connection.realm_id}"

    #     # HTTP client
    #     self.client = requests.Session()
    #     self.client.headers.update({
    #         "Authorization": f"Bearer {connection.access_token}",
    #         "Accept": "application/json",
    #         "Content-Type": "application/json"
    #     })
    def __init__(self, connection=None):
        self.connection = connection

    def query(self, query):
        """Run a SELECT query against QuickBooks API"""
        url = f"{self.base_url}/query"
        params = {"query": query}

        resp = self.client.get(url, params=params)

        # Handle auth problems
        if resp.status_code == 401:
            raise PermissionError("Unauthorized: Access token expired or invalid.")

        if resp.status_code == 403:
            raise PermissionError("Forbidden: Your app does not have permission.")

        resp.raise_for_status()
        return resp.json()

    def get_authorization_url(self, state):
        scopes = "com.intuit.quickbooks.accounting"
        # scopes = "com.intuit.quickbooks.accounting com.intuit.quickbooks.payment"

        return (
            f"{self.AUTH_BASE}"
            f"?client_id={settings.QUICKBOOKS_CLIENT_ID}"
            f"&scope={scopes}"
            f"&redirect_uri={settings.QUICKBOOKS_REDIRECT_URI}"
            f"&response_type=code"
            f"&state={state}"
        )

    def exchange_code_for_tokens(self, code, realm_id):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
        }

        auth = (settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET)

        resp = requests.post(self.TOKEN_URL, headers=headers, data=data, auth=auth)
        resp.raise_for_status()

        tokens = resp.json()

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "realm_id": realm_id,
        }

    def refresh_access_token(self):
        if not self.connection:
            raise ValueError("QuickBooks connection not provided")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.connection.refresh_token,
        }

        auth = (settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET)

        resp = requests.post(self.TOKEN_URL, headers=headers, data=data, auth=auth)
        resp.raise_for_status()

        tokens = resp.json()

        self.connection.access_token = tokens["access_token"]
        self.connection.refresh_token = tokens.get("refresh_token", self.connection.refresh_token)
        self.connection.token_expires_at = timezone.now() + timedelta(seconds=tokens["expires_in"])
        self.connection.save()

        return self.connection
    
    def fetch_accounts(self):
        """Fetch accounts with automatic token refresh and 403 handling"""
        if not self.connection:
            raise ValueError("QuickBooks connection not provided")

        # Refresh token before call
        self.refresh_access_token()

        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{self.connection.realm_id}/query"
        query = "SELECT * FROM Account"
        headers = {
            "Authorization": f"Bearer {self.connection.access_token}",
            "Accept": "application/json"
        }
        params = {"query": query}

        resp = requests.get(url, headers=headers, params=params)
        
        if resp.status_code == 403:
            raise PermissionError("Forbidden: Your sandbox company may not have access or no accounts exist.")
        resp.raise_for_status()

        return resp.json()
    
    def fetch_transactions(self, start_date=None, end_date=None):
        """
        Fetch transactions from QuickBooks.
        Optionally filter by date range.
        """
        query = "SELECT * FROM Transaction"  # You can filter by type if needed
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"

        response = self.query(query)  # Assuming self.client is QuickBooks SDK client
        return response
    

    def fetch(self, entity, start_date=None, end_date=None):
        """Generic fetch for any QuickBooks entity."""
        if not self.connection:
            raise ValueError("QuickBooks connection not provided")

        self.refresh_access_token()

        url = f"{self.BASE_URL}/{self.connection.realm_id}/query"
        query = f"SELECT * FROM {entity}"
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"

        headers = {
            "Authorization": f"Bearer {self.connection.access_token}",
            "Accept": "application/json"
        }
        resp = requests.get(url, headers=headers, params={"query": query})

        if resp.status_code == 403:
            raise PermissionError(f"Forbidden: No access or no {entity} exist")
        resp.raise_for_status()
        return resp.json().get("QueryResponse", {}).get(entity, [])
    
