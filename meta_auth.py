import hmac
import hashlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config

def generate_appsecret_proof(access_token, app_secret):
    """
    Meta Official Security: Generates HMAC-SHA256 appsecret_proof
    using the access token and app secret.
    """
    if not access_token or not app_secret:
        raise ValueError("Token or App Secret is missing.")
        
    h = hmac.new(
        app_secret.encode('utf-8'),
        msg=access_token.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    return h.hexdigest()

def get_secure_session(retry_post=True):
    """
    Returns a requests.Session configured with TLS and Retry logic.
    Retries 3 times on server errors (500, 502, 503, 504) or rate limits (429)
    with an exponential backoff (delay increases with each retry).

    retry_post=False: POST requests ko retry NAHI karega. Use this for any
    call that uploads binary data (video chunks etc.) — agar request server
    par successfully process ho gayi ho but response timeout/drop ho jaye,
    retry se duplicate/corrupted upload ban sakta hai. GET/HEAD/OPTIONS par
    retry hamesha safe hai kyunki wo side-effect-free hain.
    """
    session = requests.Session()
    
    methods = ["HEAD", "GET", "OPTIONS", "POST"] if retry_post else ["HEAD", "GET", "OPTIONS"]
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=2,  # Delays: 2s, 4s, 8s
        allowed_methods=methods
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def get_auth_payload(is_page=True):
    """
    Helper function to quickly get the base payload with Token & Proof.
    If is_page is True, uses Page Token (for FB). 
    If False, uses User Token (for IG).
    """
    token = config.PAGE_ACCESS_TOKEN if is_page else config.USER_ACCESS_TOKEN
    proof = generate_appsecret_proof(token, config.APP_SECRET)
    
    return {
        "access_token": token,
        "appsecret_proof": proof
    }

if __name__ == "__main__":
    # Quick test to verify everything is working
    try:
        payload = get_auth_payload(is_page=True)
        print("✅ meta_auth.py configured successfully!")
        print(f"🔒 AppSecret Proof Generated: {payload['appsecret_proof'][:10]}...[HIDDEN]")
        
        session = get_secure_session()
        print("🌐 Secure Session with Retry Logic Ready!")
    except Exception as e:
        print(f"❌ Error in meta_auth: {e}")