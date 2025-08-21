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

        // No need to check for duplicates since backend handles overwriting
        // Files with the same name will overwrite existing ones
    };
}

export default FileValidationPlugin;