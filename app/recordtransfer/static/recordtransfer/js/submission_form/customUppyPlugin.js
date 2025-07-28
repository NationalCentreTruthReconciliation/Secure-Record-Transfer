import { BasePlugin } from "@uppy/core";

class FileValidationPlugin extends BasePlugin {
    constructor(uppy, opts) {
        super(uppy, opts);
        this.type = "uploader";
        this.id = this.opts.id || "FileValidationPlugin";
        this.title = "File Validation Plugin";
    }

    install() {
        this.uppy.on("file-added", (file) => {
            this.validateFile(file);
        });
    }

    // This deals with the case where the user tries to upload a file with the same name as an
    // existing mock file, which wouldn't normally be caught due to the difference in file ids
    validateFile = (file) => {
        // Skip validation for mock files which represent already uploaded files
        if (file.meta?.mock) {
            return;
        }
        // Check if file name is duplicate
        const uppyFiles = this.uppy.getFiles();
        const hasDuplicate = uppyFiles.some(
            existingFile => existingFile.name === file.name && existingFile.id !== file.id
        );
        if (hasDuplicate) {
            this.uppy.info(
                window.django.gettext(
                    `Cannot add the duplicate file '${file.name}', it already exists`
                ),
                5000
            );
            this.uppy.removeFile(file.id);
            return;
        }
    };
}

export default FileValidationPlugin;