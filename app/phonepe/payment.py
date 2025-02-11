
#import jsons
import json
import base64
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def calculate_sha256_string(input_string):
    # Create a hash object using the SHA-256 algorithm
    sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    # Update hash with the encoded string
    sha256.update(input_string.encode('utf-8'))
    # Return the hexadecimal representation of the hash
    return sha256.finalize().hex()

def base64_encode(input_dict):
    # Convert the dictionary to a JSON string
    json_data = json.dumps(input_dict)
    # Encode the JSON string to bytes
    data_bytes = json_data.encode('utf-8')
    # Perform Base64 encoding and return the result as a string
    return base64.b64encode(data_bytes).decode('utf-8')

def Phonepe(amount,TransactionId,userid,mobilenumber,vendor_name,inserted_id,total_num_pages):
    #http://localhost/customer/registration?customer_name=afadf&shop_name=fasdfasd&email=pranitkalebere%40gmail.com&mobile=9172945030&location=pune&machine_id=MP07A9WN 
    INDEX = "1"
    ENDPOINT = "/pg/v1/pay"
    SALTKEY = "46926fb2-c538-4bac-b25d-d27ccdc0f65f"

    MAINPAYLOAD = {
    "merchantId": "M2226URXB6PEM",
    "merchantTransactionId": TransactionId,
    "merchantUserId": userid,
    "amount": amount,
    "redirectUrl": "https://theautodoc.in",
    "redirectMode": "REDIRECT",
    "callbackUrl": f"https://theautodoc.in/{vendor_name}/payment_callback?transactionId={TransactionId}&amount={amount}&inserted_id={inserted_id}&total_num_pages={total_num_pages}",
    "mobileNumber": mobilenumber,
    "paymentInstrument": {
        "type": "PAY_PAGE"
    }}
    print(f"https://theautodoc.in/{vendor_name}/payment_callback?transactionId={TransactionId}&amount={amount}&inserted_id={inserted_id}&total_num_pages={total_num_pages}")
    
    base64String = base64_encode(MAINPAYLOAD)
    mainString = base64String + ENDPOINT + SALTKEY
    sha256Val = calculate_sha256_string(mainString)
    checkSum = sha256Val + '###' + INDEX

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checkSum,
        'accept': 'application/json',
    }
    json_data = {
        'request': base64String,
    }
    response = requests.post('https://api.phonepe.com/apis/hermes/pg/v1/pay', headers=headers, json=json_data)
    responseData = response.json()
    return responseData['data']['instrumentResponse']['redirectInfo']['url']

def payment_validate(form_data_dict,transactionId):
    INDEX = "1"
    SALTKEY = "46926fb2-c538-4bac-b25d-d27ccdc0f65f"

    request_url = 'https://api.phonepe.com/apis/hermes/pg/v1/status/M2226URXB6PEM/' + transactionId
    sha256_Pay_load_String = '/pg/v1/status/M2226URXB6PEM/' + transactionId + SALTKEY
    sha256_val = calculate_sha256_string(sha256_Pay_load_String)
    checksum = sha256_val + '###' + INDEX
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checksum,
        'X-MERCHANT-ID': "M2226URXB6PEM"}
    
    response = requests.get(request_url, headers=headers)
    response_js = json.loads(response.text)
    return response_js.get("data").get("state")

#make payment without vendor_name for another callback url
def Payment_for_product(amount,TransactionId,email_id,mobilenumber):

    INDEX = "1"
    ENDPOINT = "/pg/v1/pay"
    SALTKEY = "46926fb2-c538-4bac-b25d-d27ccdc0f65f"

    MAINPAYLOAD = {
    "merchantId": "M2226URXB6PEM",
    "merchantTransactionId": TransactionId,
    "merchantUserId":email_id,
    "amount": amount,
    "redirectUrl": "https://www.theautodoc.in/callback",
    "redirectMode": "POST",
    "callbackUrl": "https://www.theautodoc.in/callback",
    "mobileNumber": mobilenumber,
    "paymentInstrument": {
        "type": "PAY_PAGE"
    }}
    
    base64String = base64_encode(MAINPAYLOAD)
    mainString = base64String + ENDPOINT + SALTKEY
    sha256Val = calculate_sha256_string(mainString)    
    checkSum = sha256Val + '###' + INDEX

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checkSum,
        'accept': 'application/json',
    }
    json_data = {
        'request': base64String, 
    }
    response = requests.post('https://api.phonepe.com/apis/hermes/pg/v1/pay', headers=headers, json=json_data)
    responseData = response.json()
    return responseData['data']['instrumentResponse']['redirectInfo']['url']
