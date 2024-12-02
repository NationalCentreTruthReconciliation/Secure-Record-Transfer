from recordtransfer.settings import SIGN_UP_ENABLED, MAX_SINGLE_UPLOAD_SIZE, \
    MAX_TOTAL_UPLOAD_COUNT, MAX_TOTAL_UPLOAD_SIZE, FILE_UPLOAD_ENABLED, MODE

def signup_status(request):
    return {'SIGN_UP_ENABLED': SIGN_UP_ENABLED}

def file_upload_status(request):
    return {'FILE_UPLOAD_ENABLED': FILE_UPLOAD_ENABLED}

def file_uploads(request):
    return {
        'MAX_TOTAL_UPLOAD_SIZE': MAX_TOTAL_UPLOAD_SIZE,
        'MAX_SINGLE_UPLOAD_SIZE': MAX_SINGLE_UPLOAD_SIZE,
        'MAX_TOTAL_UPLOAD_COUNT': MAX_TOTAL_UPLOAD_COUNT,
    }

def mode(request):
    return {
        'production': MODE == "production"
    }
