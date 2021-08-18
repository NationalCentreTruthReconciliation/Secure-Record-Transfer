from recordtransfer.settings import SIGN_UP_ENABLED

def signup_status(request):
    return {'SIGN_UP_ENABLED': SIGN_UP_ENABLED}
