const axios = require('axios');

class QuickBooksService {
    constructor(connection = null) {
        this.connection = connection;
        this.AUTH_BASE = "https://appcenter.intuit.com/connect/oauth2";
        this.TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer";
        this.BASE_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company";
    }

    getAuthorizationUrl(state) {
        const scopes = "com.intuit.quickbooks.accounting";
        return (
            `${this.AUTH_BASE}?client_id=${process.env.QUICKBOOKS_CLIENT_ID}` +
            `&scope=${scopes}&redirect_uri=${process.env.QUICKBOOKS_REDIRECT_URI}` +
            `&response_type=code&state=${state}`
        );
    }

    async exchangeCodeForTokens(code, realmId) {
        const data = new URLSearchParams({
            grant_type: "authorization_code",
            code: code,
            redirect_uri: process.env.QUICKBOOKS_REDIRECT_URI,
        });

        const auth = Buffer.from(
            `${process.env.QUICKBOOKS_CLIENT_ID}:${process.env.QUICKBOOKS_CLIENT_SECRET}`
        ).toString('base64');

        const resp = await axios.post(this.TOKEN_URL, data, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${auth}`
            }
        });

        return {
            access_token: resp.data.access_token,
            refresh_token: resp.data.refresh_token,
            expires_in: resp.data.expires_in,
            realm_id: realmId
        };
    }

    async refreshAccessToken() {
        if (!this.connection) {
            throw new Error("QuickBooks connection not provided");
        }

        const data = new URLSearchParams({
            grant_type: "refresh_token",
            refresh_token: this.connection.refresh_token,
        });

        const auth = Buffer.from(
            `${process.env.QUICKBOOKS_CLIENT_ID}:${process.env.QUICKBOOKS_CLIENT_SECRET}`
        ).toString('base64');

        const resp = await axios.post(this.TOKEN_URL, data, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${auth}`
            }
        });

        this.connection.access_token = resp.data.access_token;
        this.connection.refresh_token = resp.data.refresh_token || this.connection.refresh_token;
        this.connection.token_expires_at = new Date(Date.now() + resp.data.expires_in * 1000);
        await this.connection.save();

        return this.connection;
    }

    async fetchAccounts() {
        // "Fetch accounts with automatic token refresh and 403 handling"
        if (!this.connection) {
            throw new Error("QuickBooks connection not provided");
        }

        // Refresh token before call
        await this.refreshAccessToken();

        const url = `https://sandbox-quickbooks.api.intuit.com/v3/company/${this.connection.realm_id}/query`;
        const query = "SELECT * FROM Account";

        try {
            const resp = await axios.get(url, {
                headers: {
                    "Authorization": `Bearer ${this.connection.access_token}`,
                    "Accept": "application/json"
                },
                params: { query }
            });
            return resp.data;
        } catch (error) {
            if (error.response?.status === 403) {
                throw new Error("Forbidden: Your sandbox company may not have access or no accounts exist.");
            }
            throw error;
        }
    }

    async fetch(entity, startDate = null, endDate = null) {
        // "Generic fetch for any QuickBooks entity."
        if (!this.connection) {
            throw new Error("QuickBooks connection not provided");
        }

        await this.refreshAccessToken();

        let query = `SELECT * FROM ${entity}`;
        if (startDate && endDate) {
            query += ` WHERE TxnDate >= '${startDate}' AND TxnDate <= '${endDate}'`;
        }

        try {
            const resp = await axios.get(`${this.BASE_URL}/${this.connection.realm_id}/query`, {
                headers: {
                    "Authorization": `Bearer ${this.connection.access_token}`,
                    "Accept": "application/json"
                },
                params: { query }
            });
            return resp.data.QueryResponse?.[entity] || [];
        } catch (error) {
            if (error.response?.status === 403) {
                throw new Error(`Forbidden: No access or no ${entity} exist`);
            }
            throw error;
        }
    }
}

module.exports = QuickBooksService;
