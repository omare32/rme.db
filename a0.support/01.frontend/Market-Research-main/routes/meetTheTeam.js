const path = require('path');

const express = require('express');

const pagesController = require('../controller/pages');

const router = express.Router();

router.get('/meet-the-team', pagesController.meetTheTeam); 

module.exports = router;