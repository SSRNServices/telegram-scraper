const fs = require('fs');

let appVersion = "1.0.0";
try {
  appVersion = fs.readFileSync('./version.txt', 'utf8').trim();
} catch (err) {
  console.log("Could not read version.txt, defaulting to", appVersion);
}

module.exports = {
  apps: [{
    name: "telegram-scraper",
    script: "./loop.py",
    interpreter: "python3",
    version: appVersion,
    env: {
      NODE_ENV: "production",
    }
  }]
}
