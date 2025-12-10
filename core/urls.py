"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Point /api/auth/ routes to users app
    path('api/auth/', include('users.urls')),
    path('api/quickbooks/', include('quickbooks_integration.urls')),
]



# import requests
# from django.conf import settings
# from django.utils import timezone
# from datetime import timedelta

# class QuickBooksService:
#     AUTH_BASE = "https://appcenter.intuit.com/connect/oauth2"
#     TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

#     def __init__(self, connection=None):
#         self.connection = connection

#     def get_authorization_url(self, state):
#         scopes = "com.intuit.quickbooks.accounting"

#         return (
#             f"{self.AUTH_BASE}"
#             f"?client_id={settings.QUICKBOOKS_CLIENT_ID}"
#             f"&scope={scopes}"
#             f"&redirect_uri={settings.QUICKBOOKS_REDIRECT_URI}"
#             f"&response_type=code"
#             f"&state={state}"
#         )

#     def exchange_code_for_tokens(self, code, realm_id):
#         headers = {
#             "Accept": "application/json",
#             "Content-Type": "application/x-www-form-urlencoded",
#         }

#         data = {
#             "grant_type": "authorization_code",
#             "code": code,
#             "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
#         }

#         auth = (settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET)

#         resp = requests.post(self.TOKEN_URL, headers=headers, data=data, auth=auth)
#         resp.raise_for_status()

#         tokens = resp.json()

#         return {
#             "access_token": tokens["access_token"],
#             "refresh_token": tokens["refresh_token"],
#             "expires_in": tokens["expires_in"],
#             "realm_id": realm_id,
#         }

#     def refresh_access_token(self):
#         if not self.connection:
#             raise ValueError("QuickBooks connection not provided")

#         headers = {
#             "Accept": "application/json",
#             "Content-Type": "application/x-www-form-urlencoded",
#         }

#         data = {
#             "grant_type": "refresh_token",
#             "refresh_token": self.connection.refresh_token,
#         }

#         auth = (settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET)

#         resp = requests.post(self.TOKEN_URL, headers=headers, data=data, auth=auth)
#         resp.raise_for_status()

#         tokens = resp.json()

#         self.connection.access_token = tokens["access_token"]
#         self.connection.refresh_token = tokens.get("refresh_token", self.connection.refresh_token)
#         self.connection.token_expires_at = timezone.now() + timedelta(seconds=tokens["expires_in"])
#         self.connection.save()

#         return self.connection
    
#     def fetch_accounts(self):
#         """Fetch accounts with automatic token refresh and 403 handling"""
#         if not self.connection:
#             raise ValueError("QuickBooks connection not provided")

#         # Refresh token before call
#         self.refresh_access_token()

#         url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{self.connection.realm_id}/query"
#         query = "SELECT * FROM Account"
#         headers = {
#             "Authorization": f"Bearer {self.connection.access_token}",
#             "Accept": "application/json"
#         }
#         params = {"query": query}

#         resp = requests.get(url, headers=headers, params=params)
        
#         if resp.status_code == 403:
#             raise PermissionError("Forbidden: Your sandbox company may not have access or no accounts exist.")
#         resp.raise_for_status()

#         return resp.json()
    
    
