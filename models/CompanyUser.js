const mongoose = require('mongoose');

const companyUserSchema = new mongoose.Schema({
    company: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Company',
        required: true
    },
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
        unique: true
    },
    role: {
        type: String,
        required: true,
        maxlength: 100
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
    image: {
        type: String,
        default: null
    }
}, {
    timestamps: true
});

module.exports = mongoose.model('CompanyUser', companyUserSchema);
