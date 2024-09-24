// Received
exports.received = (req, res, next) => {
    res.render('received', { 
        path: '/received',
        pageTitle: 'Received'
     });
};