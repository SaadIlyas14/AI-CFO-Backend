from django.db import models
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class QuickBooksConnection(models.Model):
    """Store QuickBooks OAuth tokens and company info"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='quickbooks_connection')
    realm_id = models.CharField(max_length=255)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quickbooks_connections'
    
    def __str__(self):
        return f"QB Connection for {self.company.name}"


class QuickBooksAccount(models.Model):
    """Chart of Accounts from QuickBooks"""
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='accounts')
    qb_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100)
    account_sub_type = models.CharField(max_length=100, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    
    synced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quickbooks_accounts'
        unique_together = ['connection', 'qb_id']


class QuickBooksTransaction(models.Model):
    """Store transactions from QuickBooks"""
    TRANSACTION_TYPES = [
        ('invoice', 'Invoice'),
        ('payment', 'Payment'),
        ('expense', 'Expense'),
        ('bill', 'Bill'),
        ('purchase', 'Purchase'),
        ('journal_entry', 'Journal Entry'),
    ]
    
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='transactions')
    qb_id = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    raw_data = models.JSONField()
    synced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quickbooks_transactions'
        unique_together = ['connection', 'qb_id', 'transaction_type']


class SyncLog(models.Model):
    """Track sync operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    records_synced = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'quickbooks_sync_logs'
        ordering = ['-started_at']


class QuickBooksCustomer(models.Model):
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='customers')
    qb_id = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quickbooks_customers'
        unique_together = ['connection', 'qb_id']


class QuickBooksVendor(models.Model):
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='vendors')
    qb_id = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quickbooks_vendors'
        unique_together = ['connection', 'qb_id']


class QuickBooksInvoice(models.Model):
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='invoices')
    qb_id = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='Open')
    raw_data = models.JSONField()
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quickbooks_invoices'
        unique_together = ['connection', 'qb_id']


class QuickBooksBill(models.Model):
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='bills')
    qb_id = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='Open')
    raw_data = models.JSONField()
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quickbooks_bills'
        unique_together = ['connection', 'qb_id']


class QuickBooksPayment(models.Model):
    connection = models.ForeignKey(QuickBooksConnection, on_delete=models.CASCADE, related_name='payments')
    qb_id = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    raw_data = models.JSONField()
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quickbooks_payments'
        unique_together = ['connection', 'qb_id']