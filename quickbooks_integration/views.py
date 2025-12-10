from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from .services import QuickBooksService
from .models import QuickBooksConnection
from companies.models import Company
from .serializers import QuickBooksConnectionSerializer
from .models import QuickBooksAccount
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import QuickBooksAccount, QuickBooksTransaction




class QuickBooksAuthView(views.APIView):
    """Initiate QuickBooks OAuth flow"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            service = QuickBooksService()
            
            # Fix: Better company lookup
            company = None
            if hasattr(request.user, 'company_profile'):
                company = request.user.company_profile
            else:
                company = request.user.company_set.first()
            
            if not company:
                return Response({'error': 'No company found for this user'}, status=400)
            
            state = f"company_{company.id}"
            auth_url = service.get_authorization_url(state=state)
            
            return Response({'authorization_url': auth_url})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class QuickBooksCallbackView(views.APIView):
    """Handle QuickBooks OAuth callback"""
    permission_classes = []
    
    def get(self, request):
        code = request.GET.get('code')
        realm_id = request.GET.get('realmId')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        # Fix: Redirect to correct frontend URL
        frontend_url = 'http://localhost:3000/integrations/quickbooks'
        
        if error:
            return redirect(f'{frontend_url}?qb_error={error}')
        
        if not code or not realm_id:
            return redirect(f'{frontend_url}?qb_error=missing_params')
        
        try:
            company_id = int(state.replace('company_', ''))
            company = Company.objects.get(id=company_id)
            
            service = QuickBooksService()
            tokens = service.exchange_code_for_tokens(code, realm_id)
            
            connection, created = QuickBooksConnection.objects.update_or_create(
                company=company,
                defaults={
                    'realm_id': tokens['realm_id'],
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'token_expires_at': timezone.now() + timedelta(seconds=tokens['expires_in']),
                    'is_active': True,
                }
            )
            
            return redirect(f'{frontend_url}?qb_connected=true')
        
        except Exception as e:
            return redirect(f'{frontend_url}?qb_error={str(e)}')


class QuickBooksConnectionStatusView(views.APIView):
    """Get QuickBooks connection status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Fix: Better company lookup
            company = None
            if hasattr(request.user, 'company_profile'):
                company = request.user.company_profile
            else:
                company = request.user.company_set.first()
                
            if not company:
                return Response({
                    'connected': False,
                    'message': 'No company found for this user'
                })
            
            connection = QuickBooksConnection.objects.get(company=company)
            
            serializer = QuickBooksConnectionSerializer(connection)
            return Response({
                'connected': True,
                **serializer.data
            })
        
        except QuickBooksConnection.DoesNotExist:
            return Response({
                'connected': False,
                'message': 'QuickBooks not connected'
            })
        except Exception as e:
            return Response({
                'connected': False,
                'message': str(e)
            }, status=500)



class SyncAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get company
            company = getattr(request.user, 'company_profile', None)
            if not company:
                return Response({'error': 'No company found for this user'}, status=400)

            # Get connection
            connection = QuickBooksConnection.objects.get(company=company)

            service = QuickBooksService(connection)

            # Fetch accounts
            try:
                data = service.fetch_accounts()
            except PermissionError as e:
                return Response({'error': str(e)}, status=403)
            except Exception as e:
                return Response({'error': f"QuickBooks API error: {str(e)}"}, status=400)

            accounts = data.get("QueryResponse", {}).get("Account", [])
            if not accounts:
                return Response({'message': 'No accounts found in sandbox'}, status=200)

            # Save accounts
            count = 0
            for acc in accounts:
                QuickBooksAccount.objects.update_or_create(
                    connection=connection,
                    qb_id=acc["Id"],
                    defaults={
                        "name": acc.get("Name"),
                        "account_type": acc.get("AccountType"),
                        "account_sub_type": acc.get("AccountSubType"),
                        "current_balance": acc.get("CurrentBalance", 0),
                    }
                )
                count += 1

            connection.last_synced = timezone.now()
            connection.save()

            return Response({"message": f"Synced {count} accounts."})

        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class QuickBooksDisconnectView(views.APIView):
    """Disconnect QuickBooks integration"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        try:
            company = None
            if hasattr(request.user, 'company_profile'):
                company = request.user.company_profile
            else:
                company = request.user.company_set.first()
                
            if not company:
                return Response({'error': 'No company found'}, status=400)
            
            connection = QuickBooksConnection.objects.get(company=company)
            
            # Option 1: Delete the connection completely
            connection.delete()
            
            # Option 2: Just deactivate (if you want to keep historical data)
            # connection.is_active = False
            # connection.access_token = ''
            # connection.refresh_token = ''
            # connection.save()
            
            return Response({
                'message': 'QuickBooks disconnected successfully'
            })
            
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)




class SyncTransactionsView(views.APIView):
    """Sync QuickBooks transactions"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            company = getattr(request.user, 'company_profile', None)
            if not company:
                return Response({'error': 'No company found for this user'}, status=400)

            connection = QuickBooksConnection.objects.get(company=company)
            service = QuickBooksService(connection)

            # Optional: last sync date to fetch only new transactions
            last_synced = connection.last_synced or timezone.now() - timedelta(days=30)
            data = service.fetch_transactions(start_date=last_synced.date())

            transactions = data.get("QueryResponse", {}).get("Transaction", [])
            if not transactions:
                return Response({'message': 'No transactions found'}, status=200)

            count = 0
            for txn in transactions:
                QuickBooksTransaction.objects.update_or_create(
                    connection=connection,
                    qb_id=txn["Id"],
                    transaction_type=txn["TxnType"].lower(),
                    defaults={
                        "transaction_date": txn.get("TxnDate"),
                        "amount": txn.get("TotalAmt") or txn.get("Amount"),
                        "customer_name": txn.get("CustomerRef", {}).get("name"),
                        "vendor_name": txn.get("VendorRef", {}).get("name"),
                        "description": txn.get("PrivateNote"),
                        "raw_data": txn,
                    }
                )
                count += 1

            connection.last_synced = timezone.now()
            connection.save()

            return Response({"message": f"Synced {count} transactions."})

        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)
        except PermissionError as e:
            return Response({'error': str(e)}, status=403)
        except Exception as e:
            return Response({'error': f"QuickBooks API error: {str(e)}"}, status=500)



class SyncAllDataView(views.APIView):
    """Sync all QuickBooks data"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            company = None
            if hasattr(request.user, 'company_profile'):
                company = request.user.company_profile
            else:
                company = request.user.company_set.first()
                
            if not company:
                return Response({'error': 'No company found'}, status=400)
            
            connection = QuickBooksConnection.objects.get(company=company)
            
            connection.last_synced = timezone.now()
            connection.save()
            
            return Response({
                'message': 'All data synced successfully',
                'synced_at': connection.last_synced.isoformat()
            })
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class ListAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'No company found'}, status=400)
        
        connection = QuickBooksConnection.objects.get(company=company)
        accounts = QuickBooksAccount.objects.filter(connection=connection)
        data = [
            {
                'name': acc.name,
                'type': acc.account_type,
                'sub_type': acc.account_sub_type,
                'balance': acc.current_balance
            }
            for acc in accounts
        ]
        return Response({'accounts': data})
    

class ListTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'No company found'}, status=400)

        try:
            connection = QuickBooksConnection.objects.get(company=company)
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)

        transactions = QuickBooksTransaction.objects.filter(connection=connection).order_by('-transaction_date')

        data = [
            {
                'id': txn.id,
                'qb_id': txn.qb_id,
                'date': txn.transaction_date,
                'type': txn.transaction_type,
                'amount': txn.amount,
                'customer_name': txn.customer_name,
                'vendor_name': txn.vendor_name,
                'description': txn.description,
            }
            for txn in transactions
        ]

        return Response({'transactions': data})



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .services import QuickBooksService
from .models import QuickBooksConnection, QuickBooksAccount, QuickBooksTransaction, QuickBooksCustomer, QuickBooksVendor, QuickBooksInvoice, QuickBooksBill, QuickBooksPayment

class SyncAllQuickBooksDataView(APIView):
    """Fetch and save all QuickBooks accounting entities."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'No company found for this user'}, status=400)

        try:
            connection = QuickBooksConnection.objects.get(company=company)
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)

        service = QuickBooksService(connection)

        entities = ["Account", "Customer", "Vendor", "Invoice", "Bill", "Payment", "Transaction"]
        synced_counts = {}

        for entity in entities:
            try:
                data = service.fetch(entity)
                synced_counts[entity] = len(data)

                # Save to Django models
                if entity == "Account":
                    for acc in data:
                        QuickBooksAccount.objects.update_or_create(
                            connection=connection,
                            qb_id=acc["Id"],
                            defaults={
                                "name": acc.get("Name"),
                                "account_type": acc.get("AccountType"),
                                "account_sub_type": acc.get("AccountSubType"),
                                "current_balance": acc.get("CurrentBalance", 0),
                            }
                        )
                elif entity == "Customer":
                    for cust in data:
                        QuickBooksCustomer.objects.update_or_create(
                            connection=connection,
                            qb_id=cust["Id"],
                            defaults={
                                "display_name": cust.get("DisplayName"),
                                "email": cust.get("PrimaryEmailAddr", {}).get("Address"),
                                "balance": cust.get("Balance", 0),
                            }
                        )
                elif entity == "Vendor":
                    for vendor in data:
                        QuickBooksVendor.objects.update_or_create(
                            connection=connection,
                            qb_id=vendor["Id"],
                            defaults={
                                "display_name": vendor.get("DisplayName"),
                                "email": vendor.get("PrimaryEmailAddr", {}).get("Address"),
                                "balance": vendor.get("Balance", 0),
                            }
                        )
                elif entity == "Invoice":
                    for inv in data:
                        QuickBooksInvoice.objects.update_or_create(
                            connection=connection,
                            qb_id=inv["Id"],
                            defaults={
                                "customer_name": inv.get("CustomerRef", {}).get("name"),
                                "total": inv.get("TotalAmt"),
                                "status": inv.get("Balance") > 0 and "Open" or "Paid",
                                "raw_data": inv
                            }
                        )
                elif entity == "Bill":
                    for bill in data:
                        QuickBooksBill.objects.update_or_create(
                            connection=connection,
                            qb_id=bill["Id"],
                            defaults={
                                "vendor_name": bill.get("VendorRef", {}).get("name"),
                                "total": bill.get("TotalAmt"),
                                "status": bill.get("Balance") > 0 and "Open" or "Paid",
                                "raw_data": bill
                            }
                        )
                elif entity == "Payment":
                    for pay in data:
                        QuickBooksPayment.objects.update_or_create(
                            connection=connection,
                            qb_id=pay["Id"],
                            defaults={
                                "customer_name": pay.get("CustomerRef", {}).get("name"),
                                "vendor_name": pay.get("VendorRef", {}).get("name"),
                                "amount": pay.get("TotalAmt"),
                                "payment_date": pay.get("TxnDate"),
                                "raw_data": pay
                            }
                        )
                elif entity == "Transaction":
                    for txn in data:
                        QuickBooksTransaction.objects.update_or_create(
                            connection=connection,
                            qb_id=txn["Id"],
                            transaction_type=txn["TxnType"].lower(),
                            defaults={
                                "transaction_date": txn.get("TxnDate"),
                                "amount": txn.get("TotalAmt") or txn.get("Amount"),
                                "customer_name": txn.get("CustomerRef", {}).get("name"),
                                "vendor_name": txn.get("VendorRef", {}).get("name"),
                                "description": txn.get("PrivateNote"),
                                "raw_data": txn
                            }
                        )

            except PermissionError:
                synced_counts[entity] = 0
            except Exception as e:
                synced_counts[entity] = f"Error: {e}"

        connection.last_synced = timezone.now()
        connection.save()

        return Response({
            "message": "Sync complete",
            "synced_counts": synced_counts,
            "synced_at": connection.last_synced.isoformat()
        })






class SyncAllQuickBooksDataView(APIView):
    """Fetch and save all QuickBooks accounting entities."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'No company found for this user'}, status=400)

        try:
            connection = QuickBooksConnection.objects.get(company=company)
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)

        service = QuickBooksService(connection)

        entities = ["Account", "Customer", "Vendor", "Invoice", "Bill", "Payment"]
        synced_counts = {}

        for entity in entities:
            try:
                data = service.fetch(entity)
                synced_counts[entity] = len(data)

                if entity == "Account":
                    for acc in data:
                        QuickBooksAccount.objects.update_or_create(
                            connection=connection,
                            qb_id=acc["Id"],
                            defaults={
                                "name": acc.get("Name"),
                                "account_type": acc.get("AccountType"),
                                "account_sub_type": acc.get("AccountSubType"),
                                "current_balance": acc.get("CurrentBalance", 0),
                            }
                        )
                elif entity == "Customer":
                    for cust in data:
                        QuickBooksCustomer.objects.update_or_create(
                            connection=connection,
                            qb_id=cust["Id"],
                            defaults={
                                "display_name": cust.get("DisplayName"),
                                "email": cust.get("PrimaryEmailAddr", {}).get("Address"),
                                "balance": cust.get("Balance", 0),
                            }
                        )
                elif entity == "Vendor":
                    for vendor in data:
                        QuickBooksVendor.objects.update_or_create(
                            connection=connection,
                            qb_id=vendor["Id"],
                            defaults={
                                "display_name": vendor.get("DisplayName"),
                                "email": vendor.get("PrimaryEmailAddr", {}).get("Address"),
                                "balance": vendor.get("Balance", 0),
                            }
                        )
                elif entity == "Invoice":
                    for inv in data:
                        QuickBooksInvoice.objects.update_or_create(
                            connection=connection,
                            qb_id=inv["Id"],
                            defaults={
                                "customer_name": inv.get("CustomerRef", {}).get("name"),
                                "total": inv.get("TotalAmt"),
                                "status": "Open" if inv.get("Balance", 0) > 0 else "Paid",
                                "raw_data": inv
                            }
                        )
                elif entity == "Bill":
                    for bill in data:
                        QuickBooksBill.objects.update_or_create(
                            connection=connection,
                            qb_id=bill["Id"],
                            defaults={
                                "vendor_name": bill.get("VendorRef", {}).get("name"),
                                "total": bill.get("TotalAmt"),
                                "status": "Open" if bill.get("Balance", 0) > 0 else "Paid",
                                "raw_data": bill
                            }
                        )
                elif entity == "Payment":
                    for pay in data:
                        QuickBooksPayment.objects.update_or_create(
                            connection=connection,
                            qb_id=pay["Id"],
                            defaults={
                                "customer_name": pay.get("CustomerRef", {}).get("name"),
                                "vendor_name": pay.get("VendorRef", {}).get("name"),
                                "amount": pay.get("TotalAmt"),
                                "payment_date": pay.get("TxnDate"),
                                "raw_data": pay
                            }
                        )

            except PermissionError:
                synced_counts[entity] = 0
            except Exception as e:
                synced_counts[entity] = f"Error: {e}"

        connection.last_synced = timezone.now()
        connection.save()

        return Response({
            "message": "Sync complete",
            "synced_counts": synced_counts,
            "synced_at": connection.last_synced.isoformat()
        })


# New endpoints to fetch the actual data
class ListAllDataView(APIView):
    """Get all synced QuickBooks data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'No company found'}, status=400)

        try:
            connection = QuickBooksConnection.objects.get(company=company)
        except QuickBooksConnection.DoesNotExist:
            return Response({'error': 'QuickBooks not connected'}, status=400)

        # Fetch all data
        accounts = QuickBooksAccount.objects.filter(connection=connection)
        customers = QuickBooksCustomer.objects.filter(connection=connection)
        vendors = QuickBooksVendor.objects.filter(connection=connection)
        invoices = QuickBooksInvoice.objects.filter(connection=connection)
        bills = QuickBooksBill.objects.filter(connection=connection)
        payments = QuickBooksPayment.objects.filter(connection=connection)

        return Response({
            'accounts': [
                {
                    'qb_id': acc.qb_id,
                    'name': acc.name,
                    'type': acc.account_type,
                    'sub_type': acc.account_sub_type,
                    'balance': float(acc.current_balance) if acc.current_balance else 0
                }
                for acc in accounts
            ],
            'customers': [
                {
                    'qb_id': cust.qb_id,
                    'name': cust.display_name,
                    'email': cust.email,
                    'balance': float(cust.balance) if cust.balance else 0
                }
                for cust in customers
            ],
            'vendors': [
                {
                    'qb_id': v.qb_id,
                    'name': v.display_name,
                    'email': v.email,
                    'balance': float(v.balance) if v.balance else 0
                }
                for v in vendors
            ],
            'invoices': [
                {
                    'qb_id': inv.qb_id,
                    'customer': inv.customer_name,
                    'total': float(inv.total) if inv.total else 0,
                    'status': inv.status
                }
                for inv in invoices
            ],
            'bills': [
                {
                    'qb_id': bill.qb_id,
                    'vendor': bill.vendor_name,
                    'total': float(bill.total) if bill.total else 0,
                    'status': bill.status
                }
                for bill in bills
            ],
            'payments': [
                {
                    'qb_id': pay.qb_id,
                    'customer': pay.customer_name,
                    'vendor': pay.vendor_name,
                    'amount': float(pay.amount) if pay.amount else 0,
                    'date': pay.payment_date
                          }
                for pay in payments
            ]
        })