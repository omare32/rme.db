const {Sequelize} = require('sequelize');

const sequelize = new Sequelize('heroku_72ec84966902615', 'be92ffa00cbb3f', '90255ef3', {
  dialect: 'mysql',
  host: 'eu-cdbr-west-03.cleardb.net'
});

module.exports = sequelize;
