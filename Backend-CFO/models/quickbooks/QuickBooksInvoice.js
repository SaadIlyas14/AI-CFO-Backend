const mongoose = require('mongoose');

const quickBooksInvoiceSchema = new mongoose.Schema({
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
    customer_name: {
        type: String,
        maxlength: 255,
        default: null
    },
    total: {
        type: mongoose.Schema.Types.Decimal128,
        default: 0
    },
    status: {
        type: String,
        maxlength: 50,
        default: 'Open'
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
    collection: 'quickbooks_invoices',
    toJSON: { getters: true }
});

quickBooksInvoiceSchema.index({ connection: 1, qb_id: 1 }, { unique: true });

module.exports = mongoose.model('QuickBooksInvoice', quickBooksInvoiceSchema);
