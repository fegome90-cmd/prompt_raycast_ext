const config = require("@raycast/eslint-config");

module.exports = Array.isArray(config) ? config.flat() : config;
