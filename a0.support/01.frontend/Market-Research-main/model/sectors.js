const fs = require('fs');
const path = require('path');
const rootDir = require('../util/path');

const p = path.join(
    rootDir, 
    'data', 
    'sectors.json'
); 

const getSectorsFromFile = cb => { 
    fs.readFile(p, (err, fileContent) => {
        if (err) {
            cb([]);
        } else {
            cb(JSON.parse(fileContent));
        }
    });
};

module.exports = class Sector{
    constructor (s) {
        this.sector = s
    }

    static fetchAll(cb) {
       getSectorsFromFile(cb); 
    }
}