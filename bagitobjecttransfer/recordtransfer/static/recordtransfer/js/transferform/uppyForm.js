import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';
import XHR from '@uppy/xhr-upload';
import FileValidationPlugin from './customUppyPlugin';
import { getCookie, getSessionToken } from './utils';

document.addEventListener('DOMContentLoaded', () => {
    const settings = JSON.parse(
        document.getElementById("py_context_file_upload_settings")?.textContent
    );

    if (!settings) return;

    const maxTotalUploadSizeBytes = settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024;
    const maxSingleUploadSizeBytes = settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024;

    const uploadButton = document.getElementById('upload-button');

    const issueFileIds = [];
    

    const uppy = new Uppy(
            {
                autoProceed: false,
                restrictions: {
                    maxFileSize: maxSingleUploadSizeBytes,
                    minFileSize: 0,
                    maxTotalFileSize: maxTotalUploadSizeBytes,
                    minNumberOfFiles: 1,
                    maxNumberOfFiles: settings.MAX_TOTAL_UPLOAD_COUNT,
                    allowedFileTypes: settings.ACCEPTED_FILE_FORMATS,
                },
                onBeforeUpload: (files) => {
                    const hasIssues = Object.values(files).some(file => issueFileIds.includes(file.id));
                    if (hasIssues) {
                        uppy.info('Please remove the files with issues before proceeding.', 'error', 5000);
                        return false;
                    }
                }
            }
        )
        .use(
            Dashboard,
            {
                inline: true,
                target: '#uppy-dashboard',
                hideUploadButton: false,
                hideRetryButton: true,
                hideCancelButton: true,
                singleFileFullScreen: false,
                disableStatusBar: true,
                proudlyDisplayPoweredByUppy: false,
                width: '100%',
                disableThumbnailGenerator: true,
                showRemoveButtonAfterComplete: true,
                doneButtonHandler: null,
            }
        )
        .use(XHR, {
            endpoint: '/transfer/uploadfile/',
            method: 'POST',
            formData: true,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Upload-Session-Token': getSessionToken(),
            },
            bundle: true,
            timeout: 180000,
            limit: 2,
            responseType: 'json',
            getResponseData: (xhr) => {
                try {
                    return xhr.response;
                } catch (error) {
                    console.error('Error parsing JSON response:', error);
                    return null;
                }
            },
            onAfterResponse: (xhr, _retryCount) => {
                const issues = xhr.response.issues;
                if (issues) {
                    uppy.resetProgress();
                    const uppyFiles = uppy.getFiles();
                    xhr.response.issues.forEach((issue) => {
                        const issueFile = uppyFiles.find((file) => file.name === issue.file);
                        issueFileIds.push(issueFile.id);
                        uppy.emit('upload-error', issueFile, {name: "Upload Error", message: issue.verboseError}, xhr);
                    });
                }
            }

        })
        .use(FileValidationPlugin);

        uppy.on("complete", (result) => {
            console.log('Upload complete');
            console.log('successful files:', result.successful);
	        console.log('failed files:', result.failed);
        });

        const fileId = uppy.addFile({
            name: "myfile.pdf",
            type: "application/pdf",
            data: new Blob(),
            meta: { uploadComplete: true, uploadStarted: true },
          });

        uppy.setFileState(fileId, {
            progress: { uploadComplete: true, uploadStarted: true },
        });
    
        console.dir(uppy);

        uploadButton.addEventListener('click', () => {
            uppy.upload();
        });
});
