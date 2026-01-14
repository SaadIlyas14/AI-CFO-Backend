const mongoose = require('mongoose');

const companySchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
        unique: true
    },
    name: {
        type: String,
        required: true,
        maxlength: 255
    },
    email: {
        type: String,
        required: true,
        unique: true
    },
    phone: {
        type: String,
        required: true,
        maxlength: 20
    },
    website: {
        type: String,
        default: ''
    },
    description: {
        type: String,
        default: ''
    },
    address: {
        type: String,
        required: true,
        maxlength: 255
    },
    industry: {
        type: String,
        required: true,
        maxlength: 255
    },
    company_size: {
        type: String,
        required: true,
        maxlength: 100
    },
    plan: {
        type: String,
        maxlength: 100,
        default: null
    },
    softdelete: {
        type: Boolean,
        default: false
    },
    status: {
        type: String,
        enum: ['active', 'inactive', 'pending'],
        default: 'pending'
    },
    company_since: {
        type: String,
        default: null
    },
    last_login: {
        type: Date,
        default: null
    },
    company_logo: {
        type: String,
        default: null
    }
}, {
    timestamps: true
});

module.exports = mongoose.model('Company', companySchema);
