const express = require('express');
const app = express();
const version = process.env.VERSION || 'blue';
app.get('/', (req, res) => res.send(`Hello from ${version} version`));
app.listen(3000, () => console.log(`App ${version} listening on port 3000`));