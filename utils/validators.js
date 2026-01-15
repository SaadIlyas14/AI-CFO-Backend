const { body, validationResult } = require('express-validator');

const handleValidationErrors = (req, res, next) => {
    
    const errors = validationResult(req);
    
    if (!errors.isEmpty()) {
        console.log('Validation errors:', errors.array());
        return res.status(400).json({ errors: errors.array() });
    }
    next();
};

exports.validateSignup = [
    // Match frontend field names (snake_case)
    body('username').trim().isLength({ min: 3 }).withMessage('Username must be at least 3 characters'),
    body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
    body('confirm_password').custom((value, { req }) => {
        if (value !== req.body.password) {
            throw new Error('Passwords do not match');
        }
        return true;
    }),
    body('company_email').isEmail().withMessage('Invalid email address'),
    body('company_name').trim().notEmpty().withMessage('Company name is required'),
    body('phone').trim().notEmpty().withMessage('Phone is required'),
    body('industry').trim().notEmpty().withMessage('Industry is required'),
    body('company_size').trim().notEmpty().withMessage('Company size is required'),
    // Make captchaToken optional for now (add it to frontend later)
    // body('captchaToken').trim().notEmpty().withMessage('Captcha is required'),
    handleValidationErrors
];

exports.validateLogin = [
    body('email').isEmail().withMessage('Invalid email address'),
    body('password').trim().notEmpty().withMessage('Password is required'),
    // body('captchaToken').trim().notEmpty().withMessage('Captcha is required'),
    handleValidationErrors
];

exports.validatePasswordReset = [
    body('email').isEmail().withMessage('Invalid email address'),
    body('token').trim().notEmpty().withMessage('Token is required'),
    body('newPassword').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
    body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.newPassword) {
            throw new Error('Passwords do not match');
        }
        return true;
    }),
    handleValidationErrors
];
