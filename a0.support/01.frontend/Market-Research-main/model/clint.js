const Sequelize = require('sequelize');

const sequelize = require('../util/database');

const Clint = sequelize.define('clint', {
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
    jobTitle: {
        type: Sequelize.STRING(100),
        allowNull: false
    },
    companyName: {
        type: Sequelize.STRING(100),
        allowNull: false
    },
    workEmail: {
        type: Sequelize.STRING,
        allowNull: false,
    },
    sector: {
        type: Sequelize.STRING(100),
        allowNull: false 
    },
    description: {
        type: Sequelize.TEXT,
        allowNull: true
    }
})

module.exports = Clint;
