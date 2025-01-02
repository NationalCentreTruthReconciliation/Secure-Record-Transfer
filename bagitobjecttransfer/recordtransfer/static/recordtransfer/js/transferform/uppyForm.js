import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';
import XHR from '@uppy/xhr-upload';
import FileValidationPlugin from './customUppyPlugin';
import { getCookie } from './utils';

document.addEventListener('DOMContentLoaded', () => {
    const settings = JSON.parse(
        document.getElementById("py_context_file_upload_settings")?.textContent
    );

    if (!settings) return;

    const maxTotalUploadSizeBytes = settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024;
    const maxSingleUploadSizeBytes = settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024;

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
            }
        )
        .use(
            Dashboard,
            {
                inline: true,
                target: '#uppy-dashboard',
                hideUploadButton: false,
                singleFileFullScreen: false,
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
            },
            bundle: true,
            timeout: 180000,
            limit: 2,
            responseType: 'json',
            getResponseData(xhr) {
                try {
                    return xhr.response;
                } catch (error) {
                    console.error('Error parsing JSON response:', error);
                    return null;
                }
            }
        })
        .use(FileValidationPlugin);

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
});
