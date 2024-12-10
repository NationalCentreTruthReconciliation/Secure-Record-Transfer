const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const parentDir = path.dirname(__dirname);
const inputDir = path.join(parentDir, 'bagitobjecttransfer/recordtransfer/static/recordtransfer/img');
const outputDir = path.join(parentDir, 'dist');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// Compress and convert images to WebP
fs.readdir(inputDir, (err, files) => {
    if (err) {
        console.error('Error reading the directory:', err);
        return;
    }

    files.forEach((file) => {
        const inputFilePath = path.join(inputDir, file);
        const outputFilePath = path.join(outputDir, `${path.parse(file).name}.webp`); // Output as WebP

        // Process only image files (supported formats)
        if (/\.(jpg|jpeg|png|webp)$/i.test(file)) {
            sharp(inputFilePath)
                .webp({ quality: 80 }) // Convert to WebP with 80% quality
                .toFile(outputFilePath)
                .then(() => {
                    console.log(`Compressed and converted to WebP: ${file}`);
                })
                .catch((err) => {
                    console.error(`Error processing ${file}:`, err);
                });
        } else {
            console.log(`Skipped (not a supported image format): ${file}`);
        }
    });
});
