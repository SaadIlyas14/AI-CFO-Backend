const mongoose = require('mongoose');

const quickBooksVendorSchema = new mongoose.Schema({
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
    display_name: {
        type: String,
        required: true,
        maxlength: 255
    },
    email: {
        type: String,
        default: null
    },
    balance: {
        type: mongoose.Schema.Types.Decimal128,
        default: 0
    },
    synced_at: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true,
    collection: 'quickbooks_vendors',
    toJSON: { getters: true }
});

quickBooksVendorSchema.index({ connection: 1, qb_id: 1 }, { unique: true });

module.exports = mongoose.model('QuickBooksVendor', quickBooksVendorSchema);
