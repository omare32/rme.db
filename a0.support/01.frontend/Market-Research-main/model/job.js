const Sequelize = require('sequelize');

const sequelize = require('../util/database');

const Job = sequelize.define('job', {
    id: {
        type: Sequelize.INTEGER,
        autoIncrement: true,
        allowNull: false,
        primaryKey: true
    },
    firstName: {
        type: Sequelize.STRING(100),
        allowNull: false
    },
    lastName: {
        type: Sequelize.STRING(100),
        allowNull: false
    },
    email: {
        type: Sequelize.STRING,
        allowNull: false,
    },
    mobile: {
        type: Sequelize.STRING,
        allowNull: false
    },
    sector: {
        type: Sequelize.STRING(100),
        allowNull: false 
    },
    timePattern: {
        type: Sequelize.STRING(50),
        allowNull: false
    },
    interest: {
        type: Sequelize.TEXT,
        allowNull: true
    },
    cv: {
        type: Sequelize.STRING,
        allowNull: true
    },
    coverLetter: {
        type: Sequelize.TEXT,
        allowNull: true
    }
})

module.exports = Job;

