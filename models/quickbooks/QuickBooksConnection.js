const mongoose = require('mongoose');

const quickBooksConnectionSchema = new mongoose.Schema({
    // "Store QuickBooks OAuth tokens and company info"
    company: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Company',
        required: true,
        unique: true
    },
    realm_id: {
        type: String,
        required: true,
        maxlength: 255
    },
    access_token: {
        type: String,
        required: true
    },
    refresh_token: {
        type: String,
        required: true
    },
    token_expires_at: {
        type: Date,
        required: true
    },
    is_active: {
        type: Boolean,
        default: true
    },
    last_synced: {
        type: Date,
        default: null
    }
}, {
    timestamps: true,
    collection: 'quickbooks_connections'
});

module.exports = mongoose.model('QuickBooksConnection', quickBooksConnectionSchema);
