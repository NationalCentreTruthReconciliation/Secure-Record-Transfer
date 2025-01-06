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
} from "./utils";

document.addEventListener("DOMContentLoaded", async () => {
    const settings = getSettings();

    if (!settings) {return;}

    const maxTotalUploadSizeBytes = settings.MAX_TOTAL_UPLOAD_SIZE * 1024 * 1024;
    const maxSingleUploadSizeBytes = settings.MAX_SINGLE_UPLOAD_SIZE * 1024 * 1024;

    const uploadButton = document.getElementById("upload-button");

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
                // Add mapping of file names to file IDs as global metadata so that the server
                // can associate files with their IDs
                const fileNameToIdPairs = Object.values(files).reduce((acc, file) => {
                    acc[file.name] = file.id;
                    return acc;
                }, {});
                uppy.setMeta(fileNameToIdPairs);
            }
        }
    )
        .use(
            Dashboard,
            {
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
            }
        )
        .use(XHR, {
            endpoint: "/transfer/uploadfile/",
            method: "POST",
            formData: true,
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
            bundle: true,
            timeout: 180000,
            limit: 2,
            responseType: "json",
            getResponseData: (xhr) => {
                try {
                    console.log("XHR response:", xhr.response);
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
                const issues = xhr.response.issues;
                if (issues) {
                    uppy.resetProgress();
                    const uppyFiles = uppy.getFiles();
                    xhr.response.issues.forEach((issue) => {
                        const issueFile = uppyFiles.find((file) => file.name === issue.file);
                        issueFileIds.push(issueFile.id);
                        uppy.emit(
                            "upload-error",
                            issueFile,
                            {name: "Upload Error", message: issue.verboseError},
                            xhr
                        );
                    });
                }
                else {
                    const sessionToken = xhr.response.uploadSessionToken;
                    if (!sessionToken) {
                        console.error("No session token found in response:", xhr.response);
                        return;
                    }
                    // If session token is not already set, set it
                    if (!getSessionToken()) {
                        setSessionToken(sessionToken);
                    }
                }
            }

        })
        .use(FileValidationPlugin);

    uppy.on("complete", (result) => {
        console.log("Upload complete");
        console.log("successful files:", result.successful);
        console.log("failed files:", result.failed);
    });

    uppy.on("upload-success", (file, { body }) => {
        // If all uploads were successful, the server should return a mapping of file IDs to
        // URLs for the files
        const fileUrl = body.fileIdToUrl?.[file.id];
        if (!body.issues && fileUrl) {
            uppy.setFileState(file.id, { uploadURL: fileUrl });
        }
    });

    uppy.on("file-removed", (file) => {
        if (file.meta.mock) {
            return;
        }
        // If file had issues, remove it from the list of files with issues
        if (issueFileIds.includes(file.id)) {
            const index = issueFileIds.indexOf(file.id);
            issueFileIds.splice(index, 1);
        }
        sendDeleteRequestForFile(file.name);
    });
    
    console.dir(uppy);

    uploadButton.addEventListener("click", () => {
        uppy.upload();
    });

    const uploadedFiles = await fetchUploadedFiles();
    console.log(uploadedFiles);

    if (uploadedFiles) {
        uploadedFiles.forEach((file) => {
            console.log(file);
            const fileId = uppy.addFile({
                name: file.name,
                data: makeMockBlob(file.size),
                meta: { mock: true },
            });
            uppy.setFileState(fileId, {
                progress: { uploadComplete: true, uploadStarted: true },
                uploadURL: file.url,
            });
            
        });
    }
});
