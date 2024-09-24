const path = require('path');

const express = require('express');

const router = express.Router();

const jobsController = require('../controller/jobs');
const multer = require("multer");


const today = new Date();
const yyyy = today.getUTCFullYear();
let mm = today.getUTCMonth() + 1; // Months start at 0!
let dd = today.getUTCDate();
let th = today.getUTCHours();
let tm = today.getUTCMinutes();
let ts = today.getUTCSeconds();

// Upload Files
if (dd < 10) dd = '0' + dd;
if (mm < 10) mm = '0' + mm;

const formattedToday = dd + '-' + mm + '-' + yyyy + ' ' + th
                        + ':' + tm + ':' + ts;

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/")
  },
  filename: (req, file, cb) => {
    const firstName = req.body.firstName;
    const lastName = req.body.lastName;
    cb(null, firstName + " " + lastName + " " + formattedToday + ".pdf");
  },
})

const uploadStorage = multer({ storage: storage })

// /formss/clints-form => GET
router.get('/job-form', jobsController.getJobsInfo); 

router.post('/job-form', jobsController.postJobsData);


module.exports = router;
