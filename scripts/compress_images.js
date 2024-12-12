const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const parentDir = path.dirname(__dirname);
const inputDir = path.join(parentDir, 'bagitobjecttransfer/recordtransfer/static/recordtransfer/img');
const outputDir = path.join(parentDir, 'dist');

console.log("Running image compression...");

if (!fs.existsSync(outputDir)) {
    console.log(`Output directory "${outputDir}" does not exist. Creating...`);
    fs.mkdirSync(outputDir, { recursive: true });
}

console.log(`Reading from input directory: ${inputDir}`);

console.log(`Compressing and outputting to directory: ${outputDir}`);

// Compress and convert images to WebP
fs.readdir(inputDir, (err, files) => {
    if (err) {
        console.error(`Error reading the input directory "${inputDir}":`, err);
        return;
    }

    const promises = files.map((file) => {
        const inputFilePath = path.join(inputDir, file);
        const outputFilePath = path.join(outputDir, `${path.parse(file).name}.webp`); // Output as WebP

        // Process only supported image file formats
        if (/\.(jpg|jpeg|png|webp)$/i.test(file)) {
            return sharp(inputFilePath)
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
            return Promise.resolve();
        }
    });

    // Wait for all promises to complete
    Promise.all(promises).then(() => {
        console.log("Image compression completed.");
    });
});
