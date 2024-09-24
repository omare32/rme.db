const Job = require('../model/job');
const Sector = require('../model/sectors');


exports.getJobsInfo = (req, res, next) => {
    Sector.fetchAll(sectors => {
        res.render('jobForm', { 
            sect: sectors,
            path: '/job-form',
            pageTitle: 'Job Form'
         }); 
    });
};


exports.postJobsData = (req, res, next) => {
    const firstName = req.body.firstName;
    const lastName = req.body.lastName;
    const email = req.body.email;
    const mobile = req.body.mobile;
    const sector = req.body.sector;
    const timePattern = req.body.timePattern;
    const interest = req.body.interest;
    const cv = req.file; // ! we will save CV path in database.
    const coverLetter = req.body.coverLetter;


    return Job.create({
        firstName: firstName,
        lastName: lastName,
        email: email,
        mobile: mobile,
        sector: sector,
        timePattern: timePattern,
        interest: interest,
        cv: 'Submitted',
        coverLetter: coverLetter
    })
    .then(result => {
        res.redirect('/received');
    })
    .catch(err => console.log(err));
};
