const QuickBooksService = require('../services/quickbooks.service');
const QuickBooksConnection = require('../models/quickbooks/QuickBooksConnection');
const QuickBooksAccount = require('../models/quickbooks/QuickBooksAccount');
const QuickBooksTransaction = require('../models/quickbooks/QuickBooksTransaction');
const QuickBooksCustomer = require('../models/quickbooks/QuickBooksCustomer');
const QuickBooksVendor = require('../models/quickbooks/QuickBooksVendor');
const QuickBooksInvoice = require('../models/quickbooks/QuickBooksInvoice');
const QuickBooksBill = require('../models/quickbooks/QuickBooksBill');
const QuickBooksPayment = require('../models/quickbooks/QuickBooksPayment');
const Company = require('../models/Company');

// "Initiate QuickBooks OAuth flow"
exports.initiateAuth = async (req, res) => {
    try {
        const service = new QuickBooksService();
        
        // Fix: Better company lookup
        let company = await Company.findOne({ user: req.user._id });
        
        if (!company) {
            return res.status(400).json({ error: 'No company found for this user' });
        }
        
        const state = `company_${company._id}`;
        const auth_url = service.getAuthorizationUrl(state);
        
        return res.json({ authorization_url: auth_url });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

// "Handle QuickBooks OAuth callback"
exports.handleCallback = async (req, res) => {
    const { code, realmId, state, error } = req.query;
    
    // Fix: Redirect to correct frontend URL
    const frontend_url = 'http://localhost:3000/integrations/quickbooks';
    
    if (error) {
        return res.redirect(`${frontend_url}?qb_error=${error}`);
    }
    
    if (!code || !realmId) {
        return res.redirect(`${frontend_url}?qb_error=missing_params`);
    }
    
    try {
        const company_id = state.replace('company_', '');
        const company = await Company.findById(company_id);
        
        const service = new QuickBooksService();
        const tokens = await service.exchangeCodeForTokens(code, realmId);
        
        await QuickBooksConnection.findOneAndUpdate(
            { company: company._id },
            {
                realm_id: tokens.realm_id,
                access_token: tokens.access_token,
                refresh_token: tokens.refresh_token,
                token_expires_at: new Date(Date.now() + tokens.expires_in * 1000),
                is_active: true
            },
            { upsert: true, new: true }
        );
        
        return res.redirect(`${frontend_url}?qb_connected=true`);
    } catch (error) {
        return res.redirect(`${frontend_url}?qb_error=${error.message}`);
    }
};

// "Get QuickBooks connection status"
exports.getConnectionStatus = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        
        if (!company) {
            return res.json({
                connected: false,
                message: 'No company found for this user'
            });
        }
        
        const connection = await QuickBooksConnection.findOne({ company: company._id });
        
        if (!connection) {
            return res.json({
                connected: false,
                message: 'QuickBooks not connected'
            });
        }
        
        return res.json({
            connected: true,
            id: connection._id,
            company_name: company.name,
            realm_id: connection.realm_id,
            is_active: connection.is_active,
            last_synced: connection.last_synced,
            created_at: connection.createdAt
        });
    } catch (error) {
        return res.status(500).json({
            connected: false,
            message: error.message
        });
    }
};

// "Disconnect QuickBooks integration"
exports.disconnect = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        
        if (!company) {
            return res.status(400).json({ error: 'No company found' });
        }
        
        const connection = await QuickBooksConnection.findOne({ company: company._id });
        
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }
        
        // Option 1: Delete the connection completely
        await connection.deleteOne();
        
        return res.json({
            message: 'QuickBooks disconnected successfully'
        });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.syncAccounts = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found for this user' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const service = new QuickBooksService(connection);

        let data;
        try {
            data = await service.fetchAccounts();
        } catch (error) {
            if (error.message.includes('Forbidden')) {
                return res.status(403).json({ error: error.message });
            }
            return res.status(400).json({ error: `QuickBooks API error: ${error.message}` });
        }

        const accounts = data.QueryResponse?.Account || [];
        if (!accounts.length) {
            return res.json({ message: 'No accounts found in sandbox' });
        }

        let count = 0;
        for (const acc of accounts) {
            await QuickBooksAccount.findOneAndUpdate(
                { connection: connection._id, qb_id: acc.Id },
                {
                    name: acc.Name,
                    account_type: acc.AccountType,
                    account_sub_type: acc.AccountSubType,
                    current_balance: acc.CurrentBalance || 0,
                    synced_at: new Date()
                },
                { upsert: true }
            );
            count++;
        }

        connection.last_synced = new Date();
        await connection.save();

        return res.json({ message: `Synced ${count} accounts.` });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.syncTransactions = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found for this user' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const service = new QuickBooksService(connection);
        const lastSynced = connection.last_synced || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        
        let transactions = [];
        try {
            transactions = await service.fetch('Transaction', lastSynced.toISOString().split('T')[0]);
        } catch (error) {
            if (error.message.includes('Forbidden')) {
                return res.status(403).json({ error: error.message });
            }
            return res.status(500).json({ error: `QuickBooks API error: ${error.message}` });
        }

        if (!transactions.length) {
            return res.json({ message: 'No transactions found' });
        }

        let count = 0;
        for (const txn of transactions) {
            await QuickBooksTransaction.findOneAndUpdate(
                {
                    connection: connection._id,
                    qb_id: txn.Id,
                    transaction_type: txn.TxnType?.toLowerCase() || 'unknown'
                },
                {
                    transaction_date: txn.TxnDate,
                    amount: txn.TotalAmt || txn.Amount || 0,
                    customer_name: txn.CustomerRef?.name || null,
                    vendor_name: txn.VendorRef?.name || null,
                    description: txn.PrivateNote || null,
                    raw_data: txn,
                    synced_at: new Date()
                },
                { upsert: true }
            );
            count++;
        }

        connection.last_synced = new Date();
        await connection.save();

        return res.json({ message: `Synced ${count} transactions.` });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.syncAllData = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found for this user' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const service = new QuickBooksService(connection);
        const entities = ['Account', 'Customer', 'Vendor', 'Invoice', 'Bill', 'Payment'];
        const syncedCounts = {};

        for (const entity of entities) {
            try {
                const data = await service.fetch(entity);
                syncedCounts[entity] = data.length;

                if (entity === 'Account') {
                    for (const acc of data) {
                        await QuickBooksAccount.findOneAndUpdate(
                            { connection: connection._id, qb_id: acc.Id },
                            {
                                name: acc.Name,
                                account_type: acc.AccountType,
                                account_sub_type: acc.AccountSubType,
                                current_balance: acc.CurrentBalance || 0,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                } else if (entity === 'Customer') {
                    for (const cust of data) {
                        await QuickBooksCustomer.findOneAndUpdate(
                            { connection: connection._id, qb_id: cust.Id },
                            {
                                display_name: cust.DisplayName,
                                email: cust.PrimaryEmailAddr?.Address || null,
                                balance: cust.Balance || 0,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                } else if (entity === 'Vendor') {
                    for (const vendor of data) {
                        await QuickBooksVendor.findOneAndUpdate(
                            { connection: connection._id, qb_id: vendor.Id },
                            {
                                display_name: vendor.DisplayName,
                                email: vendor.PrimaryEmailAddr?.Address || null,
                                balance: vendor.Balance || 0,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                } else if (entity === 'Invoice') {
                    for (const inv of data) {
                        await QuickBooksInvoice.findOneAndUpdate(
                            { connection: connection._id, qb_id: inv.Id },
                            {
                                customer_name: inv.CustomerRef?.name || null,
                                total: inv.TotalAmt || 0,
                                status: (inv.Balance && inv.Balance > 0) ? 'Open' : 'Paid',
                                raw_data: inv,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                } else if (entity === 'Bill') {
                    for (const bill of data) {
                        await QuickBooksBill.findOneAndUpdate(
                            { connection: connection._id, qb_id: bill.Id },
                            {
                                vendor_name: bill.VendorRef?.name || null,
                                total: bill.TotalAmt || 0,
                                status: (bill.Balance && bill.Balance > 0) ? 'Open' : 'Paid',
                                raw_data: bill,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                } else if (entity === 'Payment') {
                    for (const pay of data) {
                        await QuickBooksPayment.findOneAndUpdate(
                            { connection: connection._id, qb_id: pay.Id },
                            {
                                customer_name: pay.CustomerRef?.name || null,
                                vendor_name: pay.VendorRef?.name || null,
                                amount: pay.TotalAmt || 0,
                                payment_date: pay.TxnDate || null,
                                raw_data: pay,
                                synced_at: new Date()
                            },
                            { upsert: true }
                        );
                    }
                }
            } catch (error) {
                syncedCounts[entity] = `Error: ${error.message}`;
            }
        }

        connection.last_synced = new Date();
        await connection.save();

        return res.json({
            message: 'Sync complete',
            synced_counts: syncedCounts,
            synced_at: connection.last_synced.toISOString()
        });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.listAccounts = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const accounts = await QuickBooksAccount.find({ connection: connection._id });
        
        const data = accounts.map(acc => ({
            name: acc.name,
            type: acc.account_type,
            sub_type: acc.account_sub_type,
            balance: parseFloat(acc.current_balance) || 0
        }));

        return res.json({ accounts: data });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.listTransactions = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const transactions = await QuickBooksTransaction.find({ connection: connection._id })
            .sort({ transaction_date: -1 });

        const data = transactions.map(txn => ({
            id: txn._id,
            qb_id: txn.qb_id,
            date: txn.transaction_date,
            type: txn.transaction_type,
            amount: parseFloat(txn.amount) || 0,
            customer_name: txn.customer_name,
            vendor_name: txn.vendor_name,
            description: txn.description
        }));

        return res.json({ transactions: data });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};

exports.listAllData = async (req, res) => {
    try {
        const company = await Company.findOne({ user: req.user._id });
        if (!company) {
            return res.status(400).json({ error: 'No company found' });
        }

        const connection = await QuickBooksConnection.findOne({ company: company._id });
        if (!connection) {
            return res.status(400).json({ error: 'QuickBooks not connected' });
        }

        const accounts = await QuickBooksAccount.find({ connection: connection._id });
        const customers = await QuickBooksCustomer.find({ connection: connection._id });
        const vendors = await QuickBooksVendor.find({ connection: connection._id });
        const invoices = await QuickBooksInvoice.find({ connection: connection._id });
        const bills = await QuickBooksBill.find({ connection: connection._id });
        const payments = await QuickBooksPayment.find({ connection: connection._id });

        return res.json({
            accounts: accounts.map(acc => ({
                qb_id: acc.qb_id,
                name: acc.name,
                type: acc.account_type,
                sub_type: acc.account_sub_type,
                balance: parseFloat(acc.current_balance) || 0
            })),
            customers: customers.map(cust => ({
                qb_id: cust.qb_id,
                name: cust.display_name,
                email: cust.email,
                balance: parseFloat(cust.balance) || 0
            })),
            vendors: vendors.map(v => ({
                qb_id: v.qb_id,
                name: v.display_name,
                email: v.email,
                balance: parseFloat(v.balance) || 0
            })),
            invoices: invoices.map(inv => ({
                qb_id: inv.qb_id,
                customer: inv.customer_name,
                total: parseFloat(inv.total) || 0,
                status: inv.status
            })),
            bills: bills.map(bill => ({
                qb_id: bill.qb_id,
                vendor: bill.vendor_name,
                total: parseFloat(bill.total) || 0,
                status: bill.status
            })),
            payments: payments.map(pay => ({
                qb_id: pay.qb_id,
                customer: pay.customer_name,
                vendor: pay.vendor_name,
                amount: parseFloat(pay.amount) || 0,
                date: pay.payment_date
            }))
        });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
};
