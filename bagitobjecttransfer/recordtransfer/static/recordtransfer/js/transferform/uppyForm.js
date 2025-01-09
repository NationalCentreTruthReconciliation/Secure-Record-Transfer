import Uppy from "@uppy/core";
import Dashboard from "@uppy/dashboard";
import XHR from "@uppy/xhr-upload";
import FileValidationPlugin from "./customUppyPlugin";
import {
    getCookie,
    getSessionToken,
    setSessionToken,
    getSettings,
    fetchUploadedFiles,
    makeMockBlob,
    sendDeleteRequestForFile,
    updateCapacityDisplay,
} from "./utils";

document.addEventListener("DOMContentLoaded", async () => {
    const settings = getSettings();
    // Don't render Uppy at all if settings are not available
    if (!settings) {return;}

    const nextButton = document.getElementById("form-next-button");
    const transferForm = document.getElementById("transfer-form");
    const issueFileIds = [];

    /**
     * Updates the display of the file capacity information on the page
     * @param {import('@uppy/core').Uppy} uppy - The Uppy instance
     * @returns {void}
     */
    const updateCapacity = (uppy) => {
        const uppyFiles = uppy.getFiles();
        const totalSize = uppyFiles.reduce((total, file) => total + file.size, 0);
        updateCapacityDisplay(uppyFiles.length, totalSize);
    };   

    const uppy = new Uppy(
        {
            autoProceed: true,
            restrictions: {
                maxFileSize: settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024,
                minFileSize: 0,
                maxTotalFileSize: settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024,
                minNumberOfFiles: 1,
                maxNumberOfFiles: settings.MAX_TOTAL_UPLOAD_COUNT,
                allowedFileTypes: settings.ACCEPTED_FILE_FORMATS,
            },
        }
    )
        .use(Dashboard, {
            inline: true,
            target: "#uppy-dashboard",
            hideUploadButton: false,
            hideRetryButton: true,
            hideCancelButton: true,
            singleFileFullScreen: false,
            disableStatusBar: true,
            proudlyDisplayPoweredByUppy: false,
            width: "100%",
            disableThumbnailGenerator: true,
            showRemoveButtonAfterComplete: true,
            doneButtonHandler: null,
            showLinkToFileUploadResult: true,
        })
        .use(XHR, {
            endpoint: "/transfer/uploadfile/",
            method: "POST",
            formData: true,
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            bundle: false,
            timeout: 180000,
            limit: 2,
            responseType: "json",
            getResponseData: (xhr) => {
                try {
                    return xhr.response;
                } catch (error) {
                    console.error("Error parsing JSON response:", error);
                    return null;
                }
            },
            onBeforeRequest(xhr) {
                xhr.setRequestHeader("Upload-Session-Token", getSessionToken());
            },
            onAfterResponse: (xhr) => {
                const {error, uploadSessionToken} = xhr.response;

                // We expect the upload session token to be included unless the server had an error
                if (xhr.status < 500 && uploadSessionToken) {
                    setSessionToken(uploadSessionToken);
                } else {
                    console.error("No session token found in response:", xhr.response);
                }

                if (error) {
                    throw new Error(error);
                }
            },
            // Attempt to retry uploads for server errors, timeouts, and rate limiting
            // Default number of retries is 3, which cannot be changed
            shouldRetry: (response) => {
                const status = response.status;
                return (
                    status >= 500 && status < 600 || 
                    status === 408 || 
                    status === 429
                );
            }

        })
        .use(FileValidationPlugin);

    uppy.on("files-added" , () => {
        updateCapacity(uppy);
    });

    uppy.on("upload-error", (file) => {
        issueFileIds.push(file.id);
    });

    uppy.on("file-removed", (file) => {
        updateCapacity(uppy);
        // If file is only selected but not uploaded yet, don't need to do anything else
        if (!file.progress.uploadComplete) {
            return;
        }
        // Remove file from the list of files with issues if it is included
        if (issueFileIds.includes(file.id)) {
            const index = issueFileIds.indexOf(file.id);
            issueFileIds.splice(index, 1);
        }
        sendDeleteRequestForFile(file.name);
    });

    // Connect the next button to the Uppy upload
    nextButton.addEventListener("click", async (event) => {
        event.preventDefault();

        // Make sure user cannot proceed to next form step if there are files with issues
        const uppyFiles = uppy.getFiles();
        const hasIssues = Object.values(uppyFiles).some(
            file => issueFileIds.includes(file.id)
        );
        if (hasIssues) {
            uppy.info(
                "Please remove the files with issues before proceeding.", 
                "error",
                5000
            );
            return;
        }
        transferForm.submit();
    });

    const uploadedFiles = await fetchUploadedFiles();

    if (uploadedFiles) {
        uploadedFiles.forEach((file) => {
            const fileId = uppy.addFile({
                name: file.name,
                data: makeMockBlob(file.size),
                meta: { mock: true },
            });
            uppy.setFileState(fileId, {
                progress: { uploadComplete: true, uploadStarted: true, percentage: 100 },
                uploadURL: file.url,
            });
            
        });
    }
});
