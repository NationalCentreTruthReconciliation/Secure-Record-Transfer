import "@uppy/core/dist/style.css";
import "@uppy/dashboard/dist/style.css";

import Uppy from "@uppy/core";
import Dashboard from "@uppy/dashboard";
import XHR from "@uppy/xhr-upload";
import FileValidationPlugin from "./customUppyPlugin";
import {
    getCookie,
    getSessionToken,
    setSessionToken,
    fetchUploadedFiles,
    makeMockBlob,
    sendDeleteRequestForFile,
    updateCapacityDisplay,
    fetchNewSessionToken,
} from "./utils";

/**
 * Sets up the Uppy widget for uploading files.
 * @param {object} context - The configuration context containing upload settings
 */
export async function setupUppy(context) {
    const reviewButton = document.getElementById("form-review-button");
    const submissionForm = document.getElementById("submission-form");
    const issueFileIds = [];

    /**
     * Updates the display of the file capacity information on the page
     * @param {import('@uppy/core').Uppy} uppy - The Uppy instance
     * @returns {void}
     */
    const updateCapacity = (uppy) => {
        const uppyFiles = uppy.getFiles();
        const totalSize = uppyFiles.reduce((total, file) => total + file.size, 0);
        updateCapacityDisplay(totalSize, context["MAX_TOTAL_UPLOAD_SIZE_MB"]);
    };

    const uppy = new Uppy(
        {
            autoProceed: true,
            restrictions: {
                maxFileSize: context["MAX_SINGLE_UPLOAD_SIZE_MB"] * 1000 * 1000,
                minFileSize: 0,
                maxTotalFileSize: context["MAX_TOTAL_UPLOAD_SIZE_MB"] * 1000 * 1000,
                minNumberOfFiles: 1,
                maxNumberOfFiles: context["MAX_TOTAL_UPLOAD_COUNT"],
                allowedFileTypes: context["ACCEPTED_FILE_FORMATS"],
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
            method: "POST",
            formData: true,
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            bundle: false,
            timeout: 180000,
            limit: 2,
            responseType: "json",
            // Turns the response into a JSON object
            getResponseData: (xhr) => {
                try {
                    return xhr.response;
                } catch (error) {
                    console.error("Error parsing JSON response:", error);
                    return null;
                }
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
            // Retry uploads for server errors, timeouts, and rate limiting
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

    reviewButton.addEventListener("click", async (event) => {
        event.preventDefault();

        // Make sure user cannot proceed to next form step if there are files with issues
        const uppyFiles = uppy.getFiles();

        if (uppyFiles.length === 0) {
            uppy.info("You must upload at least one file.", "error", 5000);
            return;
        }

        const hasIssues = Object.values(uppyFiles).some(
            file => issueFileIds.includes(file.id)
        );
        if (hasIssues) {
            uppy.info(
                "Remove the files with issues to proceed.",
                "error",
                5000
            );
            return;
        }
        submissionForm.submit();
    });

    // Set the endpoint for file upload dynamically, based on the current upload session token
    uppy.addPreProcessor(async () => {
        let sessionToken = getSessionToken();
        if (!sessionToken) {
            sessionToken = await fetchNewSessionToken();
            if (!sessionToken) {
                throw new Error("Failed to fetch new session token");
            }
            setSessionToken(sessionToken);
        }
        uppy.getPlugin("XHRUpload").setOptions({
            endpoint: `/upload-session/${sessionToken}/files/`
        });
    });

    // Add mock files to represent files that have already been uploaded to the upload session
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


    // Disable review button when uploads start or are in progress
    uppy.on("upload", disableReviewButton);
    uppy.on("upload-progress", disableReviewButton);



    // Enable review button when all uploads are complete
    uppy.on("complete", () => {
        if (reviewButton) {
            reviewButton.disabled = false;
        }
    });

    /**
     * Disables the review button to prevent form submission during uploads.
     */
    function disableReviewButton() {
        if (reviewButton) {
            reviewButton.disabled = true;
        }
    }

}
