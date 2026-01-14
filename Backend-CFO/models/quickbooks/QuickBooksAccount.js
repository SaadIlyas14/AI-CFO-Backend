const mongoose = require('mongoose');

const quickBooksAccountSchema = new mongoose.Schema({
    // "Chart of Accounts from QuickBooks"
    connection: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'QuickBooksConnection',
        required: true
    },
    qb_id: {
        type: String,
        required: true,
        maxlength: 255
    },
    name: {
        type: String,
        required: true,
        maxlength: 255
    },
    account_type: {
        type: String,
        required: true,
        maxlength: 100
    },
    account_sub_type: {
        type: String,
        maxlength: 100,
        default: null
    },
    current_balance: {
        type: mongoose.Schema.Types.Decimal128,
        default: 0
    },
    active: {
        type: Boolean,
        default: true
    },
    synced_at: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true,
    collection: 'quickbooks_accounts',
    toJSON: { getters: true }
});

quickBooksAccountSchema.index({ connection: 1, qb_id: 1 }, { unique: true });

module.exports = mongoose.model('QuickBooksAccount', quickBooksAccountSchema);
