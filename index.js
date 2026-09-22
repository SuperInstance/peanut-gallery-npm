const { spawn } = require('child_process');
const path = require('path');

module.exports = {
  gallery: async function(prompt, options = {}) {
    const args = [path.join(__dirname, 'gallery.py'), prompt];
    if (options.maxRounds) args.push('--max-rounds', String(options.maxRounds));
    if (options.producer) args.push('--producer', options.producer);
    
    return new Promise((resolve, reject) => {
      const proc = spawn('python3', args, { env: process.env });
      let stdout = '', stderr = '';
      proc.stdout.on('data', d => stdout += d);
      proc.stderr.on('data', d => stderr += d);
      proc.on('close', code => {
        if (code !== 0) reject(new Error(stderr));
        else resolve(stdout);
      });
    });
  },
};
