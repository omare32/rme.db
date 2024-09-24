const path = require('path');

const express = require('express');

const messegesController = require('../controller/messeges');

const router = express.Router();

router.get('/received', messegesController.received); 

module.exports = router;