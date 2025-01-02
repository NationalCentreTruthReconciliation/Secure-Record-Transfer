import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';

document.addEventListener('DOMContentLoaded', () => {
    const settings = JSON.parse(
        document.getElementById("py_context_file_upload_settings")?.textContent
    );

    if (!settings) return;

    const maxTotalUploadSizeBytes = settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024;
    const maxSingleUploadSizeBytes = settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024;

    const uppyDashboard = new Uppy(
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
                target: '#uppy-dashboard' ,
                hideUploadButton: true,
                singleFileFullScreen: false,
                proudlyDisplayPoweredByUppy: false,
                width: '100%',
            }
        );
    
        console.dir(uppyDashboard);
});
