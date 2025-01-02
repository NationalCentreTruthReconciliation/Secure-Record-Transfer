import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';

document.addEventListener('DOMContentLoaded', () => {
    // Extract configuration settings from the context element
    const fileUploadSettingsContextElement = document.getElementById("py_context_file_upload_settings");

    if (!fileUploadSettingsContextElement) {
        return;
    }

    const fileUploadSettings = JSON.parse(fileUploadSettingsContextElement.textContent);

    const {
        MAX_TOTAL_UPLOAD_SIZE: maxTotalUploadSize,
        MAX_SINGLE_UPLOAD_SIZE: maxSingleUploadSize,
        MAX_TOTAL_UPLOAD_COUNT: maxTotalUploadCount,
        ACCEPTED_FILE_FORMATS: acceptedFileFormats
    } = fileUploadSettings;

    const maxTotalUploadSizeBytes = maxTotalUploadSize * 1024 * 1024;

    new Uppy(
        {
            autoProceed: false,
            restrictions: {
                maxFileSize: maxSingleUploadSize,
                minFileSize: 0,
                maxTotalFileSize: maxTotalUploadSizeBytes,
                maxNumberOfFiles: maxTotalUploadCount,
                allowedFileTypes: acceptedFileFormats,
            },
            locale: {
                strings: {
                    dropHereOr: 'Drop here or %{browse}',
                    browse: 'browse',
                },
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
});
