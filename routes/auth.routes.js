const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const { validateLogin, validatePasswordReset } = require('../utils/validators');
const { uploadCompanyLogo } = require('../middleware/upload.middleware');

// Remove validateSignup - we'll validate manually in controller after multer parses data
router.post('/signup', uploadCompanyLogo.single('company_logo'), authController.signup);
router.post('/login', validateLogin, authController.login);
router.post('/password-reset-request', authController.passwordResetRequest);
router.post('/password-reset', validatePasswordReset, authController.passwordReset);

module.exports = router;
