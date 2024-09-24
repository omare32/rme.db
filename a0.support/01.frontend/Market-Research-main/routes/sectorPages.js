const path = require('path');

const express = require('express');

const sectorPagesController = require('../controller/sectorPages');

const router = express.Router();

// /sectors/health-and-social-care
router.get('/health-and-social-care', sectorPagesController.healthSocial); 

// router.get('/clints-form/:sectorName', sectorPagesController.healthSocialForm);

// /sectors/Pharmaceutical
router.get('/pharmaceutical', sectorPagesController.pharmaceutical); 

// /sectors/life-science
router.get('/life-science', sectorPagesController.lifeScience); 

// /sectors/industrial-and-manufacturing
router.get('/industrial-and-manufacturing', sectorPagesController.industManuf);


// /sectors/farming-and-agriculture
router.get('/farming-and-agriculture', sectorPagesController.farmAgri);


// /sectors/creative-industries
router.get('/creative-industries', sectorPagesController.creativeIndust);


// /sectors/food-and-beverage
router.get('/food-and-beverage', sectorPagesController.food);


// /sectors/transport-and-logistics
router.get('/transport-and-logistics', sectorPagesController.trans);


// /sectors/energy-sector
router.get('/energy-sector', sectorPagesController.energy);

module.exports = router;