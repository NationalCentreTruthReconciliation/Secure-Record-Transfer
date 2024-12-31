import { TransferDropzone } from "./transferDropzone.js";

document.addEventListener('DOMContentLoaded', () => {
    const dropzoneElement = document.getElementById("file-dropzone");
    if (dropzoneElement) {
        new TransferDropzone(dropzoneElement);
    }
});