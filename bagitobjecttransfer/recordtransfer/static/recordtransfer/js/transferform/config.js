export const maxTotalUploadSize = typeof MAX_TOTAL_UPLOAD_SIZE !== 'undefined' ? MAX_TOTAL_UPLOAD_SIZE : 256.00;
export const maxSingleUploadSize = typeof MAX_SINGLE_UPLOAD_SIZE !== 'undefined' ? MAX_SINGLE_UPLOAD_SIZE : 64.00;
export const maxTotalUploadCount = typeof MAX_TOTAL_UPLOAD_COUNT !== 'undefined' ? MAX_TOTAL_UPLOAD_COUNT : 40;
export const maxTotalUploadSizeBytes = maxTotalUploadSize * 1024 * 1024;