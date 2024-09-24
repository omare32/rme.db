const path = require('path');

const express = require('express');

const clintsController = require('../controller/clints');

const router = express.Router();

router.get('/info', clintsController.getClintsData); 

module.exports = router;