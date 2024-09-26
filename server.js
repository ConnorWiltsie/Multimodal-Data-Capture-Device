const { readFileSync, writeFileSync, existsSync } = require('fs');

const express = require('express');

const app = express();

app.get('/', (req, res) => {
    let count;

    // Check if 'count.txt' exists
    if (existsSync('./count.txt')) {
        count = readFileSync('./count.txt', 'utf8');
        console.log('count ', count);
    } else {
        // Initialize count to '0' if file doesn't exist
        count = '0';
        console.log('count.txt does not exist. Initializing count to 0.');
    }

    // Parse the count and handle NaN
    let currentCount = parseInt(count, 10);
    if (isNaN(currentCount)) {
        console.log('Invalid count value. Resetting count to 0.');
        currentCount = 0;
    }

    const newCount = currentCount + 1;

    // Write the new count as a string
    writeFileSync('./count.txt', newCount.toString());

    res.send(`
        <!DOCTYPE HTML>
        <html lang ="en">
        <head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1"/>
            <title>RPi Hosted Website</title>
        </head>
        <body>
            <h1>Welcome to my Website</h1>
            <p>This page has been viewed ${newCount} times!</p>
        </body>
        </html>
    `);
});

app.listen(5000, () => console.log('http://localhost:5000/'));
