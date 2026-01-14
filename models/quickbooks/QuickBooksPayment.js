const mongoose = require('mongoose');

const quickBooksPaymentSchema = new mongoose.Schema({
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
    vendor_name: {
        type: String,
        maxlength: 255,
        default: null
    },
    amount: {
        type: mongoose.Schema.Types.Decimal128,
        default: 0
    },
    payment_date: {
        type: Date,
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
    collection: 'quickbooks_payments',
    toJSON: { getters: true }
});

quickBooksPaymentSchema.index({ connection: 1, qb_id: 1 }, { unique: true });

module.exports = mongoose.model('QuickBooksPayment', quickBooksPaymentSchema);
