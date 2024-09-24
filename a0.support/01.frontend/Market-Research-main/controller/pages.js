const Sector = require('../model/sectors');

// Home page
exports.home = (req, res, next) => {
    res.render('index', { 
        path: '/',
        pageTitle: 'Connected Vision',
     });
};

// Meet The Team Page
exports.meetTheTeam = (req, res, next) => {
    res.render('meetTheTeam', { 
        path: '/meet-the-team',
        pageTitle: 'Meet The Team',
     });
};

// About Us Page
exports.aboutUs = (req, res, next) => {
    res.render('aboutUS', { 
        path: '/about-us',
        pageTitle: 'About us',
     });
};

// Sectors Page
exports.sectors = (req, res, next) => {
    Sector.fetchAll(sectors => {
        res.render('sectors', { 
            sect: sectors,
            path: '/sectors',
            pageTitle: 'Sectors'
         });
    });
};

// Services Page
exports.services = (req, res, next) => {
    res.render('services', { 
        path: '/services',
        pageTitle: 'Services'
     });
};


