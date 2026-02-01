/**
 * Sample JavaScript file for testing tree-sitter parsing.
 */

const fs = require('fs');
const path = require('path');

class DataProcessor {
    constructor(options = {}) {
        this.options = options;
        this.data = [];
    }

    loadData(filePath) {
        const content = fs.readFileSync(filePath, 'utf-8');
        this.data = JSON.parse(content);
        return this;
    }

    filter(predicate) {
        this.data = this.data.filter(predicate);
        return this;
    }

    map(transform) {
        this.data = this.data.map(transform);
        return this;
    }

    getResults() {
        return this.data;
    }
}

function formatNumber(num) {
    return num.toLocaleString();
}

function calculateAverage(numbers) {
    if (numbers.length === 0) return 0;
    const sum = numbers.reduce((acc, n) => acc + n, 0);
    return sum / numbers.length;
}

const multiply = (a, b) => a * b;

const divide = function(a, b) {
    if (b === 0) throw new Error('Division by zero');
    return a / b;
};

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

function main() {
    const processor = new DataProcessor({ verbose: true });
    
    const numbers = [1, 2, 3, 4, 5];
    const avg = calculateAverage(numbers);
    console.log('Average:', formatNumber(avg));
    
    const result = multiply(10, divide(20, 4));
    console.log('Result:', result);
}

module.exports = {
    DataProcessor,
    formatNumber,
    calculateAverage,
    multiply,
    divide
};
