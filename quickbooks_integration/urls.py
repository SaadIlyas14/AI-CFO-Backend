from django.urls import path
from . import views
from .views import SyncAllQuickBooksDataView

app_name = 'quickbooks'

urlpatterns = [
    path('auth/', views.QuickBooksAuthView.as_view(), name='auth'),
    path('callback/', views.QuickBooksCallbackView.as_view(), name='callback'),
    path('status/', views.QuickBooksConnectionStatusView.as_view(), name='status'),
    path('disconnect/', views.QuickBooksDisconnectView.as_view(), name='disconnect'),
    path('sync/accounts/', views.SyncAccountsView.as_view(), name='sync-accounts'),
    path('sync/transactions/', views.SyncTransactionsView.as_view(), name='sync-transactions'),
    path('sync/all/', views.SyncAllDataView.as_view(), name='sync-all'),  # Add this!
    path('accounts/', views.ListAccountsView.as_view(), name='quickbooks-accounts'),
    path('transactions/', views.ListTransactionsView.as_view(), name='quickbooks-transactions'),
    path('quickbooks/sync-all/', SyncAllQuickBooksDataView.as_view(), name='sync-all-quickbooks'),
    path('data/all/', views.ListAllDataView.as_view(), name='list-all-data'),
]
