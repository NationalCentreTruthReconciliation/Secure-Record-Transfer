from recordtransfer.settings import SIGN_UP_ENABLED

def signup_status(request):
    return {'SIGN_UP_ENABLED': SIGN_UP_ENABLED}

def file_uploads(request):
    return {
        'MAX_TOTAL_UPLOAD_SIZE': 2048,
        'MAX_SINGLE_UPLOAD_SIZE': 1024,
        'MAX_TOTAL_UPLOAD_COUNT': 80,
    }
