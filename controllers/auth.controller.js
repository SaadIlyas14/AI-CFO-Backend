const User = require('../models/User');
const Company = require('../models/Company');
const { generateToken } = require('../utils/token.utils');
const emailService = require('../services/email.service');
const crypto = require('crypto');
const axios = require('axios');

// Signup - Register new company user
exports.signup = async (req, res) => {
    try {
        console.log('Request body:', req.body);
        console.log('Request file:', req.file);

        const {
            username,
            password,
            confirm_password,
            company_name,
            company_email,
            phone,
            website,
            description,
            country,
            city,
            postal_code,
            street_address,
            industry,
            company_size,
            company_since
        } = req.body;

        // Manual validation
        const errors = [];

        if (!username || username.trim().length < 3) {
            errors.push({ field: 'username', message: 'Username must be at least 3 characters' });
        }
        if (!password || password.length < 8) {
            errors.push({ field: 'password', message: 'Password must be at least 8 characters' });
        }
        if (!confirm_password || password !== confirm_password) {
            errors.push({ field: 'confirm_password', message: 'Passwords do not match' });
        }
        if (!company_email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(company_email)) {
            errors.push({ field: 'company_email', message: 'Invalid email address' });
        }
        if (!company_name || company_name.trim().length === 0) {
            errors.push({ field: 'company_name', message: 'Company name is required' });
        }
        if (!phone || phone.trim().length === 0) {
            errors.push({ field: 'phone', message: 'Phone is required' });
        }
        if (!industry || industry.trim().length === 0) {
            errors.push({ field: 'industry', message: 'Industry is required' });
        }
        if (!company_size || company_size.trim().length === 0) {
            errors.push({ field: 'company_size', message: 'Company size is required' });
        }
        if (!website || website.trim().length === 0) {
            errors.push({ field: 'website', message: 'Website is required' });
        }
        if (!description || description.trim().length === 0) {
            errors.push({ field: 'description', message: 'Description is required' });
        }
        if (!country || country.trim().length === 0) {
            errors.push({ field: 'country', message: 'Country is required' });
        }
        if (!city || city.trim().length === 0) {
            errors.push({ field: 'city', message: 'City is required' });
        }
        if (!postal_code || postal_code.trim().length === 0) {
            errors.push({ field: 'postal_code', message: 'Postal code is required' });
        }
        if (!street_address || street_address.trim().length === 0) {
            errors.push({ field: 'street_address', message: 'Street address is required' });
        }
        if (!company_since || company_since.trim().length === 0) {
            errors.push({ field: 'company_since', message: 'Company founded year is required' });
        }

        // If there are validation errors, return them
        if (errors.length > 0) {
            return res.status(400).json({ 
                error: 'Validation failed',
                errors: errors 
            });
        }

        // Check if user already exists
        const existingUser = await User.findOne({ 
            $or: [{ username }, { email: company_email }] 
        });
        if (existingUser) {
            return res.status(400).json({ error: 'User already exists with this username or email' });
        }

        // Check if company email already exists
        const existingCompany = await Company.findOne({ email: company_email });
        if (existingCompany) {
            return res.status(400).json({ error: 'Company with this email already exists' });
        }

        // Create user
        const user = new User({
            username,
            email: company_email,
            password,
            is_company: true
        });

        await user.save();

        // Create company
        const address = `${street_address}, ${city}, ${postal_code}, ${country}`;
        const company = new Company({
            user: user._id,
            name: company_name,
            email: company_email,
            phone,
            website: website || '',
            description: description || '',
            address,
            industry,
            company_size,
            company_since: company_since || null,
            company_logo: req.file ? req.file.path : null, // Save uploaded file path
            status: 'pending'
        });

        await company.save();

        // Generate tokens
        const tokens = generateToken(user._id);

        return res.status(201).json({
            message: 'User registered successfully',
            user: {
                id: user._id,
                username: user.username,
                companyEmail: user.email
            },
            tokens
        });
    } catch (error) {
        console.error('Signup error:', error);
        return res.status(500).json({ error: error.message });
    }
};

// Login
exports.login = async (req, res) => {
    try {
        const { email, password } = req.body;

        // Find company by email
        const company = await Company.findOne({ email }).populate('user');
        if (!company) {
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        const user = company.user;

        // Authenticate user
        const isPasswordValid = await user.comparePassword(password);
        if (!isPasswordValid) {
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        // Generate tokens
        const tokens = generateToken(user._id);

        return res.status(200).json({
            message: 'Login successful',
            user: {
                id: user._id,
                username: user.username,
                companyEmail: company.email,
                companyName: company.name
            },
            tokens
        });
    } catch (error) {
        console.error('Login error:', error);
        return res.status(500).json({ error: error.message });
    }
};

// Password Reset Request
exports.passwordResetRequest = async (req, res) => {
    try {
        const { email } = req.body;

        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ error: 'User with this email does not exist.' });
        }

        // Generate reset token
        const resetToken = crypto.randomBytes(32).toString('hex');
        user.reset_token = resetToken;
        await user.save();

        // Send email
        await emailService.sendPasswordResetEmail(email, resetToken);

        return res.status(200).json({ message: 'Password reset link sent to email.' });
    } catch (error) {
        console.error('Password reset request error:', error);
        return res.status(500).json({ error: error.message });
    }
};

// Password Reset
exports.passwordReset = async (req, res) => {
    try {
        const { email, token, newPassword, confirmPassword } = req.body;

        if (newPassword !== confirmPassword) {
            return res.status(400).json({ error: 'Passwords do not match.' });
        }

        const user = await User.findOne({ email, reset_token: token });
        if (!user) {
            return res.status(400).json({ error: 'Invalid or expired token.' });
        }

        user.password = newPassword;
        user.reset_token = null;
        await user.save();

        return res.status(200).json({ message: 'Password has been reset successfully.' });
    } catch (error) {
        console.error('Password reset error:', error);
        return res.status(500).json({ error: error.message });
    }
};
