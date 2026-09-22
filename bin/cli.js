#!/usr/bin/env node
const { gallery } = require('../index.js');

(async () => {
  const prompt = process.argv[2];
  if (!prompt) {
    console.error('Usage: peanut-gallery "your prompt"');
    process.exit(1);
  }
  const result = await gallery(prompt);
  console.log(result);
})();
