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

const updateCapacity = (uppy) => {
    const uppyFiles = uppy.getFiles();
    const totalSize = uppyFiles.reduce((total, file) => total + file.size, 0);
    updateCapacityDisplay(uppyFiles.length, totalSize);
};

document.addEventListener("DOMContentLoaded", async () => {
    const settings = getSettings();
    // Don't render Uppy at all if settings are not available
    if (!settings) {return;}

    const nextButton = document.getElementById("form-next-button");
    const transferForm = document.getElementById("transfer-form");
    const issueFileIds = [];

    const uppy = new Uppy(
        {
            autoProceed: false,
            restrictions: {
                maxFileSize: settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024,
                minFileSize: 0,
                maxTotalFileSize: settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024,
                minNumberOfFiles: 1,
                maxNumberOfFiles: settings.MAX_TOTAL_UPLOAD_COUNT,
                allowedFileTypes: settings.ACCEPTED_FILE_FORMATS,
            },
            onBeforeUpload: (files) => {
                const hasIssues = Object.values(files).some(
                    file => issueFileIds.includes(file.id)
                );
                if (hasIssues) {
                    uppy.info(
                        "Please remove the files with issues before proceeding.", 
                        "error",
                        5000
                    );
                    return false;
                }
                // Include mapping of file names to file IDs within global metadata so that the
                // server can associate files with their IDs
                const fileNameToIdPairs = Object.values(files).reduce((acc, file) => {
                    acc[file.name] = file.id;
                    return acc;
                }, {});
                uppy.setMeta(fileNameToIdPairs);
            }
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
            bundle: true,
            timeout: 180000,
            limit: 2,
            responseType: "json",
            getResponseData: (xhr) => {
                try {
                    const uppyFiles = uppy.getFiles();
                    const { issues } = xhr.response;
                    
                    // Reset progress of all files that were not mocked (already uploaded)
                    // so that another attempt can be made to upload them
                    uppyFiles.forEach(file => {
                        if(!file.meta.mock) {
                            uppy.setFileState(file.id, {
                                progress: { uploadComplete: false }
                            });
                        }
                    }); 

                    // Display errors and keep track of files that had issues during upload
                    if (issues) {
                        issues.forEach(issue => {
                            const issueFile = uppyFiles.find(file => file.name === issue.file);
                            uppy.setFileState(issueFile.id, {
                                error: issue.error || issue.verboseError 
                            });
                            uppy.info(issue.verboseError || issue.error, "error", 5000);
                            issueFileIds.push(issueFile.id);
                        });
                    }
                    return xhr.response;
                } catch (error) {
                    console.error("Error parsing JSON response:", error);
                    return null;
                }
            },
            onBeforeRequest(xhr) {
                xhr.setRequestHeader("Upload-Session-Token", getSessionToken());
            },
            onAfterResponse: (xhr, retryCount) => {
                const uppyFiles = uppy.getFiles();
                const {issues, uploadSessionToken} = xhr.response;

                // Remove unuploaded files if server error occurs after 3 retries
                if (retryCount >=3 && xhr.status >= 500) {
                    uppy.info("Server error. Please try again later.", "error", 5000);
                    uppyFiles.forEach(file => !file.meta.mock && uppy.removeFile(file.id));
                    return;
                }
                if (issues) {
                    return;
                }
                if (!uploadSessionToken) {
                    console.error("No session token found in response:", xhr.response);
                    return;
                }
                setSessionToken(uploadSessionToken);
            }

        })
        .use(FileValidationPlugin);

    uppy.on("upload-success", (file, { body }) => {
        // If all uploads were successful, the server should return a mapping of file IDs to
        // URLs for the files
        const fileUrl = body.fileIdToUrl?.[file.id];
        if (!body.issues && fileUrl) {
            uppy.setFileState(file.id, { uploadURL: fileUrl });
        }
    });

    uppy.on("files-added" , () => {
        updateCapacity(uppy);
    });

    uppy.on("file-removed", (file) => {
        updateCapacity(uppy);
        // If file is only selected but not uploaded yet, don't need to do anything else
        if (!file.progress.uploadComplete) {
            return;
        }
        // If file had issues, remove it from the list of files with issues
        if (issueFileIds.includes(file.id)) {
            const index = issueFileIds.indexOf(file.id);
            issueFileIds.splice(index, 1);
        }
        else {
            sendDeleteRequestForFile(file.name);
        }
    });

    // Connect the next button to the Uppy upload
    nextButton.addEventListener("click", async (event) => {
        event.preventDefault();
        uppy.setOptions({"disabled": true});
        const result = await uppy.upload();
        // Allow form to submit if there were no errors in the upload
        if (result.failed.length === 0) {
            transferForm.submit();
        }
        uppy.setOptions({"disabled": false});
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
