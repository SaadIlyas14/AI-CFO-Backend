const mongoose = require('mongoose');

const quickBooksTransactionSchema = new mongoose.Schema({
    // "Store transactions from QuickBooks"
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
    transaction_type: {
        type: String,
        required: true,
        enum: ['invoice', 'payment', 'expense', 'bill', 'purchase', 'journal_entry'],
        maxlength: 50
    },
    transaction_date: {
        type: Date,
        required: true
    },
    amount: {
        type: mongoose.Schema.Types.Decimal128,
        required: true
    },
    customer_name: {
        type: String,
        maxlength: 255,
        default: null
    },
    vendor_name: {
        type: String,
        maxlength: 255,
        default: null
    },
    description: {
        type: String,
        default: null
    },
    raw_data: {
        type: mongoose.Schema.Types.Mixed,
        required: true
    },
    synced_at: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true,
    collection: 'quickbooks_transactions',
    toJSON: { getters: true }
});

quickBooksTransactionSchema.index({ connection: 1, qb_id: 1, transaction_type: 1 }, { unique: true });

module.exports = mongoose.model('QuickBooksTransaction', quickBooksTransactionSchema);
