// Health and Social Care 
exports.healthSocial = (req, res, next) => {
    res.render('sectors/healthSocial', { 
        path: '/sectors/health-social',
        pageTitle: 'Health and Social Care'
    });
};

// exports.healthSocialForm = (req, res, next) => {
//     sectName = req.params.sectorName;
//     console.log(sectName);
//     res.render('sectors/healthSocial', {
//         path: '/clintsForm'
//     })
// }

// exports.postHealthSocial = (req, res, next) => {
//     const sectorName = req.body.pageTitle;
//     console.log(sectorName);
//     res.redirect('/clints-form')
// };

// Pharmaceutical
exports.pharmaceutical = (req, res, next) => {
    res.render('sectors/pharm', { 
        path: '/sectors/pharmaceutical',
        pageTitle: 'Pharmaceutical'
    });
};

// Life Science
exports.lifeScience = (req, res, next) => {
    res.render('sectors/lifeSci', { 
        path: '/sectors/life-science',
        pageTitle: 'Life Science'
    });
};

// Industrial and Manufacturing
exports.industManuf = (req, res, next) => {
    res.render('sectors/industManuf', { 
        path: '/sectors/industrial-and-manufacturing',
        pageTitle: 'Industrial and Manufacturing'
    });
};

// Farming and Agriculture
exports.farmAgri = (req, res, next) => {
    res.render('sectors/farmAgri', { 
        path: '/sectors/farming-and-agriculture',
        pageTitle: 'Farming and Agriculture'
    });
};

// Creative Industries
exports.creativeIndust = (req, res, next) => {
    res.render('sectors/creativeIndust', { 
        path: '/sectors/creative-industries',
        pageTitle: 'Creative Industries'
    });
};

// Food and Beverage
exports.food = (req, res, next) => {
    res.render('sectors/food', { 
        path: '/sectors/food-and-beverage',
        pageTitle: 'Food and Beverage',
        // prev: PORT
    });
};

// Transport and Logistics
exports.trans = (req, res, next) => {
    res.render('sectors/trans', { 
        path: '/sectors/transport-and-logistics',
        pageTitle: 'Transport and Logistics'
    });
};

// Energy Sector
exports.energy = (req, res, next) => {
    res.render('sectors/energy', { 
        path: '/sectors/energy-sector',
        pageTitle: 'Energy Sector'
    });
};

