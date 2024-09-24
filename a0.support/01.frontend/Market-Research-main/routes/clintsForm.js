const path = require('path');

const express = require('express');

const rootDir = require('../util/path');

const router = express.Router();

const clintsController = require('../controller/clints');
const pagesController = require('../controller/pages');
const sectorPagesController = require('../controller/sectorPages');

// clints-form => GET
router.get('/clints-form', clintsController.getCLintsInfo); 

// router.get('/clints-form', pagesController.getSectorsData);

// clints-form => POST
router.post('/clints-form', clintsController.postClintsInfo); 

// clints-form => POST
// router.post('/clints-form', sectorPagesController.postHealthSocial); 
 

module.exports = router;