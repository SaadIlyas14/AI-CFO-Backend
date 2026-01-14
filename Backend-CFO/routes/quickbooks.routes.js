const express = require('express');
const router = express.Router();
const { isAuthenticated } = require('../middleware/auth.middleware');
const qbController = require('../controllers/quickbooks.controller');

router.get('/auth', isAuthenticated, qbController.initiateAuth);
router.get('/callback', qbController.handleCallback);
router.get('/status', isAuthenticated, qbController.getConnectionStatus);
router.delete('/disconnect', isAuthenticated, qbController.disconnect);
router.post('/sync/accounts', isAuthenticated, qbController.syncAccounts);
router.post('/sync/transactions', isAuthenticated, qbController.syncTransactions);
router.post('/sync/all', isAuthenticated, qbController.syncAllData);
router.get('/accounts', isAuthenticated, qbController.listAccounts);
router.get('/transactions', isAuthenticated, qbController.listTransactions);
router.get('/data/all', isAuthenticated, qbController.listAllData);

module.exports = router;
