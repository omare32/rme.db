const path = require('path');

const http = require('http');

const bodyParser = require('body-parser');
const express = require('express');
const app = express();
const flash = require('connect-flash');

const sequelize = require('./util/database');
const session = require('express-session');
const MySQLStore = require('express-mysql-session')(session);
const helmet = require('helmet')
const compression = require('compression');



app.set('view engine', 'ejs');
app.set('views', 'views');

//app.use(helmet());
// app.use(compression());

app.use(
  helmet.contentSecurityPolicy({
    useDefaults: false,
    directives: {
      "default-src": helmet.contentSecurityPolicy.dangerouslyDisableDefaultSrc,
      scriptSrc: ["'self'", "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/intlTelInput.min.js", "https://app.simplefileupload.com/buckets/74ee161dfbe3d1cbe2a90a11b60c5c82.js"]
    },
  })
);


const clintsForm = require('./routes/clintsForm');
const jobForm = require('./routes/jobForm');
const clintsData = require('./routes/clintsData');
const homePage = require('./routes/index');
const meetTheTeam = require('./routes/meetTheTeam');
const aboutUs = require('./routes/aboutUs');
const sectors = require('./routes/sectors');
const services = require('./routes/services');
const sectorPages = require('./routes/sectorPages');
const messeges = require('./routes/messeges');
const auth = require('./routes/auth');


app.use(bodyParser.urlencoded({extended: false}));

// to link css files with html files
app.use(express.static(path.join(__dirname)));
app.use(flash());


// Pages Routes
app.use(clintsForm);
app.use(jobForm);
app.use(clintsData);
app.use(homePage);
app.use(meetTheTeam);
app.use(aboutUs);
app.use(sectors);
app.use(services);
app.use(messeges);
app.use('/sectors', sectorPages);
app.use(auth);




sequelize
// .sync({force: true})
.sync()
.then(result => {
    app.listen(process.env.PORT || 3000);
})
.catch(err => console.log(err));
