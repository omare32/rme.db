const Clint = require('../model/clint');
const Sector = require('../model/sectors');

exports.getCLintsInfo = (req, res, next) => {
    sectName = req.query.sectorName;
    // console.log(sectName);
    Sector.fetchAll(sectors => {
        res.render('clintsForm', { 
            sect: sectors,
            path: '/clints-form',
            pageTitle: 'Contact us',
            sectorName: sectName
         });
    })

};


exports.postClintsInfo = (req, res, next) => {
    const firstName = req.body.firstName;
    const lastName = req.body.lastName;
    const jobTitle = req.body.jobTitle;
    const companyName = req.body.companyName;
    const workEmail = req.body.workEmail;
    const sector = req.body.sector;
    const description = req.body.description;

    return Clint.create({
        firstName: firstName,
        lastName: lastName,
        jobTitle:jobTitle,
        companyName: companyName,
        workEmail: workEmail,
        sector: sector,
        description: description
    })
    .then(result => {
        res.redirect('/received');
    })
    .catch(err => console.log(err));
};


// table
exports.getClintsData = (req, res, next) => {
    Clint.findAll()
        .then(products => {
            return res.render('clintsInfo', { 
                prods: products, 
                pageTitle: 'Clints Data', 
                path: '/info'
                // hasClints: products.length > 0,
            });
        })
        .catch(err => console.log(err));
};