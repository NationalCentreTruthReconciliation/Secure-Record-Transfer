import { BasePlugin } from '@uppy/core';
import { getCookie, getSessionToken } from './utils';

class FileValidationPlugin extends BasePlugin {
    constructor(uppy, opts) {
        super(uppy, opts);
        this.type = 'uploader';
        this.id = this.opts.id || 'FileValidationPlugin';
        this.title = 'File Validation Plugin';
    }

    install() {
        this.uppy.on('file-added', (file) => {
            this.validateFile([file.id]);
        })
    }

    validateFile = (fileID) => {
        const file = this.uppy.getFile(fileID);
        return new Promise((resolve, reject) => {
            // This is used to skip validation for mock files which represent already uploaded files
            if (file.meta?.uploadComplete) {
                resolve();
                return;
            }
            fetch('/transfer/checkfile/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Upload-Session-Token': getSessionToken()
                },
                body: new URLSearchParams({
                    filename: file.name,
                    filesize: file.size
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.accepted) {
                    this.uppy.removeFile(fileID);
                    this.uppy.info(data.verboseError || data.error, 'error', 5000);
                    reject(new Error(data.error));
                } else {
                    resolve();
                }
            })
            .catch(error => {
                this.uppy.removeFile(fileID);
                this.uppy.info('File was not accepted', 'error', 5000);
                reject(new Error('File was not accepted'));
            });
        });
    }
}

export default FileValidationPlugin;