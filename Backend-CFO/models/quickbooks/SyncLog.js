const mongoose = require('mongoose');

const syncLogSchema = new mongoose.Schema({
    // "Track sync operations"
    connection: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'QuickBooksConnection',
        required: true
    },
    sync_type: {
        type: String,
        required: true,
        maxlength: 50
    },
    status: {
        type: String,
        enum: ['pending', 'in_progress', 'completed', 'failed'],
        default: 'pending',
        maxlength: 20
    },
    records_synced: {
        type: Number,
        default: 0
    },
    error_message: {
        type: String,
        default: null
    },
    started_at: {
        type: Date,
        default: Date.now
    },
    completed_at: {
        type: Date,
        default: null
    }
}, {
    timestamps: false,
    collection: 'quickbooks_sync_logs'
});

syncLogSchema.index({ started_at: -1 });

module.exports = mongoose.model('SyncLog', syncLogSchema);
