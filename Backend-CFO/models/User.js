const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
    username: {
        type: String,
        required: true,
        unique: true
    },
    email: {
        type: String,
        required: true,
        unique: true
    },
    password: {
        type: String,
        required: true
    },
    is_company: {
        type: Boolean,
        default: false
    },
    is_company_user: {
        type: Boolean,
        default: false
    },
    softdelete: {
        type: Boolean,
        default: false
    },
    reset_token: {
        type: String,
        default: null
    }
}, {
    timestamps: true
});

// Hash password before saving
userSchema.pre('save', async function(next) {
    if (!this.isModified('password')) return next();
    this.password = await bcrypt.hash(this.password, 10);
    next();
});

// Method to compare password
userSchema.methods.comparePassword = async function(candidatePassword) {
    return await bcrypt.compare(candidatePassword, this.password);
};

// Method to get company
userSchema.methods.getCompany = async function() {
    if (this.is_company) {
        const Company = mongoose.model('Company');
        return await Company.findOne({ user: this._id });
    } else if (this.is_company_user) {
        const CompanyUser = mongoose.model('CompanyUser');
        const companyUser = await CompanyUser.findOne({ user: this._id }).populate('company');
        return companyUser ? companyUser.company : null;
    }
    return null;
};

module.exports = mongoose.model('User', userSchema);
