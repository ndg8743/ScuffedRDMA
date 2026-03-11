const express = require('express');
const multer = require('multer');
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const router = express.Router();
const upload = multer({
  dest: os.tmpdir(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB max
  fileFilter: (req, file, cb) => {
    const allowed = [
      'application/octet-stream',
      'application/x-executable',
      'application/x-elf',
      'text/plain',
      'text/x-c',
      'text/x-asm',
    ];
    cb(null, true); // accept all for now, validate content later
  },
});

// POST /api/upload — upload a binary or source file
router.post('/', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = req.file.path;
    const originalName = req.file.originalname;
    const ext = path.extname(originalName).toLowerCase();

    // If it's a text file (.c, .s, .asm, .pseudo), read directly
    if (['.c', '.s', '.asm', '.pseudo', '.txt'].includes(ext)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      fs.unlinkSync(filePath);
      return res.json({
        content,
        inputType: ext === '.c' ? 'source' : 'assembly',
        filename: originalName,
      });
    }

    // For binary files, use objdump to disassemble
    const result = await new Promise((resolve, reject) => {
      execFile('objdump', ['-d', '-M', 'intel', '--no-show-raw-insn', filePath], {
        maxBuffer: 5 * 1024 * 1024,
        timeout: 30000,
      }, (err, stdout, stderr) => {
        if (err) {
          // Try as raw binary
          execFile('objdump', ['-d', '-b', 'binary', '-m', 'i386:x86-64', '-M', 'intel', filePath], {
            maxBuffer: 5 * 1024 * 1024,
            timeout: 30000,
          }, (err2, stdout2) => {
            if (err2) reject(new Error('Could not disassemble binary. Ensure it is a valid ELF/PE executable.'));
            else resolve(stdout2);
          });
        } else {
          resolve(stdout);
        }
      });
    });

    fs.unlinkSync(filePath);

    res.json({
      content: result,
      inputType: 'assembly',
      filename: originalName,
    });
  } catch (err) {
    console.error('Upload error:', err.message);
    if (req.file?.path) {
      try { fs.unlinkSync(req.file.path); } catch {}
    }
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;
