import { TransferDropzone } from "./transferDropzone.js";

document.addEventListener('DOMContentLoaded', () => {
    const dropzoneElement = document.getElementById("file-dropzone");
    const transferDropzone = new TransferDropzone(dropzoneElement);
    console.dir(transferDropzone);
});