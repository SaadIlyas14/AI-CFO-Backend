from rest_framework import serializers
from .models import QuickBooksConnection, QuickBooksAccount, QuickBooksTransaction, SyncLog


class QuickBooksConnectionSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = QuickBooksConnection
        fields = ['id', 'company_name', 'realm_id', 'is_active', 'last_synced', 'created_at']


class QuickBooksAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickBooksAccount
        fields = ['id', 'qb_id', 'name', 'account_type', 'current_balance', 'synced_at']


class QuickBooksTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickBooksTransaction
        fields = ['id', 'qb_id', 'transaction_type', 'transaction_date', 'amount', 'description', 'synced_at']


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = ['id', 'sync_type', 'status', 'records_synced', 'error_message', 'started_at', 'completed_at']