from flask import Flask, request, render_template, jsonify, send_from_directory,redirect, url_for, flash, session,render_template_string,send_file
from io import BytesIO
import secrets
import os
import random
import shortuuid
import requests
import pyotp
import pytz
import pymongo
import io
from flask_compress import Compress
from phonepe.payment import Payment_for_product,calculate_sha256_string,Phonepe
from kafka.config import KafkaConfig
from kafka.producer import KafkaProducer
import csv
from io import StringIO
from database.minio_file_process import stream_to_minio
from minio import Minio
#from minio.error import S3Error
from doc_process.ms_processor import get_page_count2
#from pathlib import Path
from bson import ObjectId
from bson.binary import Binary
from smtp.otp import otp_verification,send_license_key
from datetime import datetime, timedelta
#from multiprocessing import Process
from pypdf import PdfWriter ,PdfReader
ist = pytz.timezone('Asia/Kolkata')


minio_client = Minio(
    "minio:9000",   
    access_key="AKIAIOSFODNN7EXAMPLE",
    secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    secure=False, )

BUCKET_NAME = "pranit"
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)
transaction_bucket = "transactions"
if not minio_client.bucket_exists(transaction_bucket):
    minio_client.make_bucket(transaction_bucket)
config = KafkaConfig()
producer = KafkaProducer(config)
    
# constuct a function decorator to prevent unauthorized access
def is_authorized(func):
    def wrapper(*args, **kwargs):
        if 'email' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login_page'))
    return wrapper


# ---->>> API<<<-----#
uri = "mongodb+srv://admin:AutoDoc2024@atlascluster.ywbey.mongodb.net/?retryWrites=true&w=majority&appName=AtlasCluster"
client = pymongo.MongoClient(uri) 

# ---->>> vendor client<<<-----#
vendor_db = client['vendor_data']
vendor_collection = vendor_db['vendor_collection']
transactions = vendor_db['transactions']
#----------------------------------------------------------------------------------------#

#-----------------------------------------------------------------------------------------#
def generate_random_key():
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    # Generate a string of 16 random characters from the specified set
    return ''.join(random.choice(characters) for _ in range(16))


# ---->>> flask app<<<-----#
application = Flask(__name__,subdomain_matching=True)
app = application
Compress(app)
app.secret_key = secrets.token_hex(32)
app.config['SERVER_NAME'] = 'autodoc.test'
@app.before_request
def ensure_session_accessed():
    session.modified = True
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

app.config['DEBUG'] = True
app.config['ENV'] = 'production'


# ---->>> Routes<<<-----#
@app.route('/',subdomain='www')
def index_page():
    return render_template('index.html')  
@app.route("/privacy",subdomain='www')
def google_pay():
    return render_template("googlePay.html")
@app.route("/refund",subdomain='www')
def privacy():
    return render_template("refund.html")
@app.route("/terms",subdomain='www')
def terms():
    return render_template('terms.html')
@app.route("/ads.txt",subdomain='www')
def serve_ads_txt():
    # Define the path to the static directory
    static_folder = os.path.join(os.getcwd(), 'static')

    # Serve the ads.txt file from the static folder
    return send_from_directory(static_folder, 'ads.txt', mimetype='text/plain')

@app.route('/customer/registration', methods=['GET'],subdomain='www')
def register_customer():
    customer_name = request.args.get('customer_name')
    shop_name = request.args.get('shop_name')
    email = request.args.get('email') 
    mobile = request.args.get('mobile')
    location = request.args.get('location')
    machine_id = request.args.get('machine_id')
    
    customer_data = {
        "customer_name": customer_name,
        "shop_name": shop_name,
        "email": email,
        "mobile": mobile,
        "location": location,
        "machine_id": machine_id
    }
    session["customer_data"] = customer_data
    session['otp'] = str(otp_verification(email )) 
    if email is None:
        return redirect(url_for('index_page'))  

    return render_template_string(open('otp_verification.html').read(), email=email, error=None)

@app.route('/verify-otp', methods=['POST'],subdomain='www')
def verify_otp():
    email = request.form['email']
    otp = request.form['otp']
    correct_otp = session.get('otp')
    
    if otp == correct_otp:
        session.pop('otp', None) 
        mobilenumber = session.get('customer_data')['mobile']
        transaction_id_product = shortuuid.uuid()   
        session["tid_product"] = transaction_id_product
        pay_page_url = Payment_for_product(amount=199900,TransactionId=transaction_id_product,email_id=email,mobilenumber=int(mobilenumber))
        if pay_page_url:
            
            html_content = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Redirecting to Payment</title>
                <meta http-equiv="refresh" content="0; url={pay_page_url}">
            </head>
            <body>
                <h1>Redirecting to Payment...</h1>
                <p>If you are not redirected automatically, <a href="{pay_page_url}">click here</a>.</p>
            </body>
            </html>
            '''
            return render_template_string(html_content)
        else:
            html_content = '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Fail</title>
            </head>
            <body>
                <h1>Payment Failed</h1>
                <p>Please try again.</p>                
            </body>
            </html>
            '''
            return render_template_string(html_content)
    else:
        error_message = "Invalid OTP. Please try again."
        return render_template_string(
            open('otp_verification.html').read(),
            email=email,
            error=error_message)

@app.route("/callback", methods=['POST'],subdomain='www')
def callback():
    transactionId = session.get("tid_product",None)
    licenses = vendor_db["licenses"]
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
    response_js = response.json()
    is_valid = response_js.get("code")
    response_amount = response_js.get("data", {}).get("amount", 0)   

    try:
        if is_valid =="PAYMENT_SUCCESS" and float(response_amount)==1999.0:
            license_key = ""
            email = session.get('customer_data')['email']
            name = session.get('customer_data')['customer_name']
            shop_name = session.get('customer_data')['shop_name']
            mobile = session.get('customer_data')['mobile']
            location = session.get('customer_data')['location']
            machine_id = session.get('customer_data')['machine_id']
            while True:
                uuid_value = generate_random_key()
                licensekey = f"{uuid_value[:4].upper()}-{uuid_value[4:8].upper()}-{uuid_value[8:12].upper()}-{uuid_value[12:16].upper()}"

                if not organisation_admin_collection.find_one({"_id": licensekey}):
                    license_key = licensekey
                    break         
            
            vendor_collection.insert_one({
                "vendor_name": str(shop_name).replace(" ","").lower(),
                "owner_name" :name,
                "_id":license_key,
                "email":email,
                "Pan Card":None,
                "Account Number":None,
                "IFSC":None,
                'UPI':None,
                "location": location,
                "Mobile_no": mobile
            })
            
            license_document = {
                "_id": license_key,
                "vendor_name": str(shop_name).replace(" ","").lower(),
                "machine_id_1": machine_id,
                "machine_id_2": None,
                "registered": True,
                "creation_date": datetime.utcnow().replace(tzinfo=pytz.utc),
                "expiry_date": datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=365)}
            
            licenses.insert_one(license_document)
                        
            send_license_key(email, license_key,name,mobile,shop_name,location)
        return redirect(url_for('registration_success', email=email))
    except Exception as e:
        print(e)
        return redirect(url_for('index_page'))

@app.route('/registration/success', methods=['GET'],subdomain='www')
def registration_success():
    email = request.args.get('email')
    return f"Registration successful for {email}!"

@app.route('/update_profile/<vendor_name>',subdomain='business')
def update_profile(vendor_name):   

    customer_name = request.args.get('name')
    account_number = request.args.get('account_number')
    ifsc = request.args.get('ifsc')
    upi_id = request.args.get('upi_id')
    pan = request.args.get('pan')   
    location = request.args.get('location') 

    request_param = ["owner_name","Account Number","ifsc","upi_id","pan","location"]
    request_list = [customer_name,account_number,ifsc,upi_id,pan,location]
    updated_dict = {}
    # get the not null values from request list and instert only these values in updated dict
    for i in range(len(request_list)):
        if request_list[i] != "":
            updated_dict[request_param[i]] = request_list[i]
    
    if updated_dict:  # Ensure there's something to update
        vendor_collection.update_one(
        {'vendor_name': vendor_name},
        {"$set": updated_dict}
        )
    # create a  html here to show sucessfully update data and return here
    html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Profile Update</title>
            </head>
            <body>
                <h1>Profile Update Successfully</h1>
                {updated_dict}            
            </body>
            </html>
    """
    return render_template_string(html_content)
            

@app.route('/', subdomain="business")
def business_home():
       return "<h1>Welcome to the Business Portal of AutoDoc</h1>"







# ---->>> vendor <<<-----#
@app.route('/<vendor_name>',subdomain='www')
def upload_page(vendor_name):                                                     # Done
    validation = vendor_collection.find_one({"vendor_name": vendor_name })
    if validation:
        return render_template('upload.html', vendor_name=vendor_name)
    elif not validation:
        return redirect(url_for('index_page'))


@app.route('/<vendor_name>/upload', methods=['POST'],subdomain='www')
def upload_files(vendor_name):
    try:
        # Connect to the database
        pdf_collection = vendor_db[vendor_name]
        response = vendor_collection.find_one({"vendor_name": vendor_name})

        # Retrieve vendor-specific price
        if response:
            vendor_price = 100 * response.get("price", 1)
            vendor_price = round(vendor_price)
        else:
            flash('Vendor not found!', 'error')
            return redirect(url_for('upload_page', vendor_name=vendor_name))

        # Retrieve uploaded files and form data
        files = request.files.getlist('fileInput[]')
        copies_list = request.form.getlist('copies[]')
        file_group_count = int(request.form.get('fileGroupCount', 1))
        page_ranges = request.form.getlist('pageRangeType[]')
        custom_ranges_from =  request.form.getlist('pageRangeFrom[]')
        custom_ranges_to =  request.form.getlist('pageRangeTo[]')
        
        transaction_id = shortuuid.uuid()
        user_id = request.form.get('mobile_number')
        payment_method = request.form.get('payment')
        

        # Initialize lists to hold file options
        orientations_list = []
        colors_list = []
        sides_list = []

        # Retrieve file options for each group and each file
        for group in range(file_group_count):
            orientations = [request.form.get(f'orientation[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'orientation[{group+1}][{i}]') is not None]
            colors = [request.form.get(f'color[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'color[{group+1}][{i}]') is not None]
            sides = [request.form.get(f'side[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'side[{group+1}][{i}]') is not None ]

            orientations_list.extend(orientations)
            colors_list.extend(colors)
            sides_list.extend(sides)

        # Basic validation
        if not files:
            flash('No files uploaded!', 'error')
            return redirect(url_for('upload_page', vendor_name=vendor_name))

        if not (len(files) == len(copies_list) == len(orientations_list) == len(colors_list) == len(sides_list)):
            flash('File, copies, orientation, color, or side data mismatch!', 'error')
            return redirect(url_for('upload_page', vendor_name=vendor_name))

        pdf_files = []
        total_num_pages = 0
        total_amount = 0
        inserted_ids = []

        # Process each file
        for i, file in enumerate(files):
            filename = file.filename.lower()
            extension = filename.rsplit('.', 1)[1]
            
            if extension == 'pdf':

                #return redirect(url_for('upload_page', vendor_name=vendor_name))
                
                pdf_data = file.read()  
                pdf_file = io.BytesIO(pdf_data) 
                reader = PdfReader(pdf_file)
                num_pages = len(reader.pages)
                #print(num_pages)
                #pdf_document.close()

            if extension == "doc" or extension == "docx" or extension =='csv' or extension == "xls" or extension == 'xlsx' or extension == 'ppt' or extension == 'pptx':
                num_pages,pdf_data,file = get_page_count2(docx_file=file)
                
            
            # Retrieve options for the current file
            copies = int(copies_list[i]) if i < len(copies_list) else 1
            orientation = orientations_list[i] if i < len(orientations_list) else 'portrait'
            color = colors_list[i] if i < len(colors_list) else 'bw'
            side = sides_list[i] if i < len(sides_list) else 'single'
            page_range_type = page_ranges[i] if i < len(page_ranges) else 'all'
            page_range_from = int(custom_ranges_from[i]) if i < len(custom_ranges_from) and custom_ranges_from[i] else 1
            page_range_to = int(custom_ranges_to[i]) if i < len(custom_ranges_to) and custom_ranges_to[i] else num_pages
            
            # Validate page range
            if page_range_type == 'custom' and (page_range_from > page_range_to or page_range_to > num_pages):
                flash(f'Invalid custom page range for file: {filename}.', 'error')
                return redirect(url_for('upload_page', vendor_name=vendor_name))

            # Adjust page count based on the selected page range
            if page_range_type == 'custom':
                num_pages = page_range_to - page_range_from + 1
            elif page_range_type == 'firstHalf':
                num_pages = num_pages // 2
            elif page_range_type == 'secondHalf':
                num_pages = (num_pages + 1) // 2
            elif page_range_type == 'evenPages':
                num_pages = len([p for p in range(1, num_pages + 1) if p % 2 == 0])
            elif page_range_type == 'oddPages':
                num_pages = len([p for p in range(1, num_pages + 1) if p % 2 != 0])

            total_pages = num_pages * copies
            total_num_pages += total_pages
            total_amount += total_pages * vendor_price
           
            pdf_files.append({
                'vendor': vendor_name,
                'filename': filename,
                'pdf_data': pdf_data,
                "file":file,
                'num_pages': total_pages,
                'copies': copies,
                'orientation': orientation,
                'color': color,
                'side': side,
                'page_range_from': page_range_from,
                'page_range_to': page_range_to
            })
        if payment_method == "online":
            # Store the files in the database
            for pdf_file in pdf_files:
                try:
                    document = {
                        'vendor': pdf_file['vendor'],
                        "number": user_id,
                        'filename': pdf_file['filename'],
                        'filedata': Binary(pdf_file['pdf_data']),
                        'upload_time': datetime.utcnow().replace(tzinfo=pytz.utc),
                        'copies': pdf_file['copies'],
                        'orientation': pdf_file['orientation'],
                        'color': pdf_file['color'],
                        'side': pdf_file['side'],
                        'page_range_from': pdf_file.get('page_range_from'),
                        'page_range_to': pdf_file.get('page_range_to')
                    }
                    inserted_id = pdf_collection.insert_one(document).inserted_id
                    inserted_ids.append(str(inserted_id))
                except Exception as e:
                    flash(f'Error saving file {pdf_file["filename"]} to the database: {str(e)}', 'error')

            if not total_num_pages:
                flash('No valid pages found in uploaded files.', 'error')
                return redirect(url_for('upload_page', vendor_name=vendor_name))

            session['ids'] = inserted_ids
            session["amt"] = total_amount
            session["tnp"] = total_num_pages
            print(total_num_pages)

            pay_page_url = Phonepe(amount=total_amount,TransactionId=transaction_id,userid=user_id,mobilenumber=int(user_id),vendor_name=vendor_name,inserted_id=inserted_ids,total_num_pages=total_num_pages)
            if pay_page_url:
                # Render HTML with JavaScript to POST data to the payment URL
                html_content = f'''
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Redirecting to Payment</title>
                        <meta http-equiv="refresh" content="0; url={pay_page_url}">
                    </head>
                    <body>
                        <h1>Redirecting to Payment...</h1>
                        <p>If you are not redirected automatically, <a href="{pay_page_url}">click here</a>.</p>
                    </body>
                    </html>
                    '''
            return render_template_string(html_content)
        
        elif payment_method == "cash":
            for pdf_file in pdf_files:
                try:
                    document = {
                        'vendor': pdf_file['vendor'],
                        "number": user_id,
                        "payment_mode": "cash",
                        "num_pages":pdf_file['num_pages'],
                        'filename': pdf_file['filename'],
                        #'filedata': Binary(pdf_file['pdf_data']),
                        'upload_time': datetime.utcnow().replace(tzinfo=pytz.utc),
                        'copies': pdf_file['copies'],
                        'orientation': pdf_file['orientation'],
                        'color': pdf_file['color'],
                        'side': pdf_file['side'],
                        'page_range_from': pdf_file.get('page_range_from'),
                        'page_range_to': pdf_file.get('page_range_to'),
                        "printed":False
                    }
                    # inserted_id = pdf_collection.insert_one(document)
                    new_transaction = {
                        "transaction_id": None,
                        "amount": pdf_file['num_pages'] * vendor_price,
                        "File Name": pdf_file['filename'],
                        "payment_mode": "Cash",
                        "total_pages": pdf_file['num_pages'],
                        "date": datetime.utcnow().isoformat()
                    }
                    # transactions.update_one({"_id": vendor_name},{"$push": {"transactions": new_transaction}},upsert=True )
                    object_key = f"{pdf_file['vendor']}/{pdf_file['filename']}"
                    stream_to_minio(
                    file=file,
                    minio_client=minio_client,
                    bucket_name=BUCKET_NAME,
                    metadata = document,
                    object_key=object_key
                    )
                    csv_output = StringIO()
                    csv_writer = csv.DictWriter(csv_output, fieldnames=new_transaction.keys())
                    csv_writer.writeheader()
                    csv_writer.writerow(new_transaction)

                    # Get the CSV content
                    csv_data = csv_output.getvalue().encode('utf-8')
                    
                    #bucket_name = "transactions"
                    object_name = f"{pdf_file['vendor']}/transaction_{new_transaction['date']}.csv"
                    minio_client.put_object(bucket_name=transaction_bucket, object_name=object_name, data=BytesIO(csv_data), length=len(csv_data),content_type='text/csv')
                    csv_output.close()
                    message = {"vendor":pdf_file['vendor'], "data": f"{pdf_file['filename']}"}   
                    producer.produce(message,topic=pdf_file['vendor'])
                    producer.flush()
                                
                except Exception as e:
                    flash(f'Error saving file {pdf_file["filename"]} to the database: {str(e)}', 'error')

            if not total_num_pages:
                flash('No valid pages found in uploaded files.', 'error')
                return redirect(url_for('upload_page', vendor_name=vendor_name))
            return redirect(url_for('index_page'))
        

    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('upload_page', vendor_name=vendor_name))    
    
def merge_pdfs(pdf_list, orientations):
    writer = PdfWriter()  # PdfWriter to merge PDFs
    
    for i, pdf_data in enumerate(pdf_list):
        pdf_data.seek(0) 
        reader = PdfReader(pdf_data) 
        
        orientation = orientations[i] 
    
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            
            if orientation == 'landscape':
                page =page.rotate(90) 
            
            writer.add_page(page)
    
    merged_pdf = BytesIO()
    writer.write(merged_pdf) 
    merged_pdf.seek(0) 
    
    return merged_pdf 

@app.route('/<vendor_name>/serve_pdf')
def serve_pdf(vendor_name):
    inserted_ids = session.get('ids', [])
    pdf_collection = vendor_db[vendor_name]
    pdf_list = []
    orientations = []
    
    for _id in inserted_ids:
        id = ObjectId(_id)
        pdf_data_db = pdf_collection.find_one({'_id': id})
        if pdf_data_db and 'filedata' in pdf_data_db:
            pdf_data = BytesIO(pdf_data_db['filedata'])
            pdf_list.append(pdf_data)

            orientation = pdf_data_db.get("orientation", "portrait") 
            orientations.append(orientation)
    
    merged_pdf = merge_pdfs(pdf_list, orientations) 
    return send_file(merged_pdf, download_name="Updated.pdf", as_attachment=False, mimetype='application/pdf')
        
@app.route('/<vendor_name>/create_order', methods=['GET','POST'])
def create_order(vendor_name):
    if request.method == 'GET':
        return render_template('index.html') 
    
    if request.method == 'POST':
        try:
            pdf_collection = vendor_db[vendor_name]
            amount = request.form.get('amount')
            user_id = request.form.get('contact')
            transaction_id = shortuuid.uuid()
            session["tid"] = transaction_id
            inserted_ids = session.get('ids', [])
            total_num_pages= session.get("tnp",None)
            for _id in inserted_ids:
                id = ObjectId(_id)
                pdf_collection.update_one({'_id': id}, {'$set': {'number': user_id}})
            amount = int(float(amount))
            pay_page_url = Phonepe(amount=amount,TransactionId=transaction_id,userid=user_id,mobilenumber=int(user_id),vendor_name=vendor_name,inserted_id=inserted_ids,total_num_pages=total_num_pages)
            
            if pay_page_url:
                # Render HTML with JavaScript to POST data to the payment URL
                html_content = f'''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Redirecting to Payment</title>
                    <meta http-equiv="refresh" content="0; url={pay_page_url}">
                </head>
                <body>
                    <h1>Redirecting to Payment...</h1>
                    <p>If you are not redirected automatically, <a href="{pay_page_url}">click here</a>.</p>
                </body>
                </html>
                '''
                return render_template_string(html_content)
            else:
                return redirect(url_for("index_page"))
        except Exception as e:
            print(e)
            return redirect(url_for("index_page"))
    
@app.route('/<vendor_name>/payment_callback', methods=["GET",'POST'],subdomain='www')
def payment_callback(vendor_name):
    if request.method == 'GET':
        return redirect(url_for('index_page')) 
    inserted_ids = request.args.get("inserted_id")
    total_amount = request.args.get("amount")
    total_num_pages= request.args.get("total_num_pages")
    
    transactionId = request.args.get('transactionId')
    pdf_collection = vendor_db[vendor_name]
    transactionId = str(transactionId)
    inserted_ids = eval(inserted_ids)
    total_num_pages = eval(total_num_pages)
    total_amount = eval(total_amount)
    INDEX = "1"
    SALTKEY = "46926fb2-c538-4bac-b25d-d27ccdc0f65f"
    request_url = 'https://api.phonepe.com/apis/hermes/pg/v1/status/M2226URXB6PEM/' + transactionId
    sha256_Pay_load_String = '/pg/v1/status/M2226URXB6PEM/' + transactionId + SALTKEY
    sha256_val = calculate_sha256_string(sha256_Pay_load_String)
    checksum = sha256_val + '###' + INDEX
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checksum,
        'X-MERCHANT-ID': "M2226URXB6PEM"
        }    
    response = requests.get(request_url, headers=headers)
    response_js = response.json()
    is_valid = response_js.get("code")
    response_amount = response_js.get("data", {}).get("amount", 0)
    #print(is_valid,response_amount,transactionId,total_num_pages,total_amount,inserted_ids)
    try:
        if is_valid =="PAYMENT_SUCCESS" and float(response_amount)==float(total_amount):
            for _id in inserted_ids:
                id = ObjectId(_id)
                pdf_collection.update_one({'_id': id}, {'$set': {'printed': False}})
            update = {
                "$inc": {
                "total_num_pages": total_num_pages,
                "total_amount": round((total_amount/100),2)}}
            vendor_collection.update_one({'vendor_name': vendor_name}, update)
            new_transaction = {
                "transaction_id": transactionId,
                "amount": round((total_amount/100),2),
                "File Name": None,
                "payment_mode": "Online",
                "Payment_status": "Success",
                "total_pages": total_num_pages,
                "date": datetime.utcnow().isoformat()
            }
            transactions.update_one(
                {"_id": vendor_name},
                {"$push": {"transactions": new_transaction}},
                upsert=True
                )            
            return redirect(url_for('index_page'))
        else :
            for _id in inserted_ids:
                id = ObjectId(_id)
                pdf_collection.delete_one({"_id": id})
            new_transaction = {
                "transaction_id": transactionId,
                "amount": round((total_amount/100),2),
                "File Name": None,
                "payment_mode": "Online",
                "Payment_status": "Failed",
                "total_pages": total_num_pages,
                "date": datetime.utcnow().isoformat()
            }
            return redirect(url_for("index_page"))      
            
        return redirect(url_for("index_page"))
        
    except Exception as e:
        print(e)
        return redirect(url_for('index_page'))




# ---->>> organisation admin <<<-----#
organisation_db = client['organisation']
organisation_admin_collection = organisation_db['admin_collection']
organisation_collection = organisation_db['organisation_collection']



# ---->>> private <<<-----#
@app.route("/<organisation>",subdomain="private")
def private_index_page(organisation):                                            #Done
    validation = organisation_admin_collection.find_one({"organisation_name": organisation })
    if not validation:
        return render_template("private_upload.html",organisation=organisation)
    else:
        return redirect(url_for('index_page'))
    
@app.route('/<organisation>/upload', methods=['POST'],subdomain="private")
def organisation_upload_files(organisation):                                     #Done 
    
    pdf_collection = organisation_db[organisation+"pdf"]
    

    # Retrieve uploaded files, copies, and orientations
    files = request.files.getlist('fileInput[]')
    copies_list = request.form.getlist('copies[]')
    file_group_count = int(request.form.get('fileGroupCount', 1))
    page_ranges = request.form.getlist('pageRangeType[]')
    custom_ranges_from =  request.form.getlist('pageRangeFrom[]')
    custom_ranges_to =  request.form.getlist('pageRangeTo[]')

    # Initialize lists to hold file options
    orientations_list = []
    colors_list = []
    sides_list = []

    # Retrieve file options for each group and each file
    for group in range(file_group_count):
        orientations = [request.form.get(f'orientation[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'orientation[{group+1}][{i}]') is not None]
        colors = [request.form.get(f'color[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'color[{group+1}][{i}]') is not None]
        sides = [request.form.get(f'side[{group+1}][{i}]') for i in range(len(files)) if request.form.get(f'side[{group+1}][{i}]') is not None ]

        orientations_list.extend(orientations)
        colors_list.extend(colors)
        sides_list.extend(sides)

    if not files:
        flash('No files uploaded!', 'error')
        return redirect(url_for('private_index_page', organisation=organisation))

    pdf_files = []
    total_num_pages = 0
    inserted_ids_org = []

    # Ensure the lengths of all lists match
    if not (len(files) == len(copies_list) == len(orientations_list) == len(colors_list) == len(sides_list)):
        flash('File, copies, orientation, color, or side data mismatch!', 'error')
        return redirect(url_for('private_upload_page', organisation= organisation))

    for i, file in enumerate(files):
        filename = file.filename.lower()
        extension = filename.rsplit('.', 1)[1]
        if not filename:
            continue


        if extension == 'pdf':

            pdf_data = file.read()  
            pdf_file = io.BytesIO(pdf_data) 
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)

        if extension == "doc" or extension == "docx" or extension =='csv' or extension == "xls" or extension == 'xlsx' or extension == 'ppt' or extension == 'pptx':
            num_pages,pdf_data = get_page_count2(docx_file=file)

        # Retrieve options for the current file
        copies = int(copies_list[i]) if i < len(copies_list) else 1
        orientation = orientations_list[i] if i < len(orientations_list) else 'portrait'
        color = colors_list[i] if i < len(colors_list) else 'bw'
        side = sides_list[i] if i < len(sides_list) else 'single'
        page_range_type = page_ranges[i] if i < len(page_ranges) else 'all'
        page_range_from = int(custom_ranges_from[i]) if i < len(custom_ranges_from) and custom_ranges_from[i] else 1
        page_range_to = int(custom_ranges_to[i]) if i < len(custom_ranges_to) and custom_ranges_to[i] else num_pages

        # Validate page range
        if page_range_type == 'custom' and (page_range_from > page_range_to or page_range_to > num_pages):
            flash(f'Invalid custom page range for file: {filename}.', 'error')
            return redirect(url_for('private_upload_page', organisation=organisation))
        
        # Adjust page count based on the selected page range
        if page_range_type == 'custom':
            num_pages = page_range_to - page_range_from + 1
        elif page_range_type == 'firstHalf':
            num_pages = num_pages // 2
        elif page_range_type == 'secondHalf':
            num_pages = (num_pages + 1) // 2
        elif page_range_type == 'evenPages':
            num_pages = len([p for p in range(1, num_pages + 1) if p % 2 == 0])
        elif page_range_type == 'oddPages':
            num_pages = len([p for p in range(1, num_pages + 1) if p % 2 != 0])
        
        total_pages = num_pages * copies
        total_num_pages += total_pages
         

        pdf_files.append({
            'organisation': organisation,
            'filename': filename,
            'pdf_data': pdf_data,
            'num_pages': total_pages,
            'copies': copies,
            'orientation': orientation,
            'color': color,
            'side': side,
            'page_range_from': page_range_from,
            'page_range_to': page_range_to
        })
        

    # Insert files into the database
    for pdf_file in pdf_files:
        document = {
            'organisation': pdf_file['organisation'],
            'filename': pdf_file['filename'],
            'filedata': Binary(pdf_file['pdf_data']),
            'upload_time': datetime.utcnow().replace(tzinfo=pytz.utc),
            'copies': pdf_file['copies'],
            'orientation': pdf_file['orientation'],
            'color': pdf_file['color'],
            'side': pdf_file['side'],
            'page_range_from': pdf_file.get('page_range_from'),
            'page_range_to': pdf_file.get('page_range_to')
        }
        
        inserted_id = pdf_collection.insert_one(document).inserted_id
        inserted_ids_org.append(str(inserted_id))      
    print(inserted_ids_org)

    session['inserted_ids_org'] = inserted_ids_org
    if not total_num_pages:
        return redirect(url_for('private_index_page', organisation=organisation))
    return render_template('private_result.html', total_num_pages=total_num_pages, organisation=organisation)

@app.route("/<organisation>/authentication",methods=['POST'],subdomain="private")
def check_credentials(organisation):                                             #Done 
    user_id = request.form.get('user_id')
    password = request.form.get('password')
    organisation_collection = organisation_db[organisation]
    pdf_collection = organisation_db[organisation]
    inserted_ids_org = session.get('inserted_ids_org', []) 

    user = organisation_collection.find_one({"_id": user_id})
    if user and user['password'] == password:
        for id in inserted_ids_org:
            id = ObjectId(id)
            pdf_collection.update_one(
            {'_id': id},
            {'$set': {'printed': False}})  
        return jsonify({"status": "success","message": "Login successful. Files are uploaded.",
                        "redirect_url": url_for('private_index_page', organisation=organisation)}), 200
    return jsonify({"status": "error", "message": "Invalid User ID or Password. Please try again."})

@app.route('/<organisation>/management', methods=['GET', 'POST'],subdomain="private")
def private_management_login(organisation):                                      #Done 
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        password = request.form.get('password')
        admin = organisation_admin_collection.find_one({"email": admin_id})
        

        if admin and admin['password'] == password:
            session['management_id'] = admin_id
            return jsonify({"status": "success", "message": "Login successful", "redirect_url": url_for('management_dashboard', organisation=organisation)}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401

    return render_template('private_admin_login.html', organisation=organisation)

@app.route("/<organisation>/logout",subdomain="private")
def management_logout(organisation):
    session.pop('management_id', None) 
    return redirect(url_for('private_management_login',organisation=organisation))

@app.route("/<organisation>/management/dashboard",subdomain="private")
def management_dashboard(organisation):                                          #Done 
    if 'management_id' not in session:
        return redirect(url_for('private_management_login', organisation=organisation))
    return render_template("management_dashboard.html",organisation=organisation)

@app.route("/<organisation>/management/add_member", methods=['POST'],subdomain="private")
def add_member(organisation):                                                    #Done 
    if 'management_id' not in session:
        return redirect(url_for('private_management_login',organisation=organisation))
    organisation_collection = organisation_db[organisation]
    
    if request.method == 'POST':
        member_name = request.form.get('member_name')
        mobileNumber = request.form.get('mobileNumber')
        userid = request.form.get('userid')
        print(userid)
        password = request.form.get('password')
        member_id = request.form.get("member_id")        

        # Check if the vendor already exists
        if organisation_collection.find_one({"_id": userid}):
            print(organisation_collection.find_one({"_id": userid}))
            return jsonify({"status": "error", "message": "Member already exists."}), 400
        else:
            # Add the new vendor to the database
            organisation_collection.insert_one({
                "member_id":member_id,
                "member_name": str(member_name).replace(" ","").lower(),
                "mobileNumber":mobileNumber,
                "_id":userid,
                "password": password,})
            
            return jsonify({"status": "success", "message": "Member added successfully."}), 200

    return render_template('add_member.html',organisation=organisation)




# ---->>> admin client<<<-----#
db_admin = client['admin_info']
admin_collection = db_admin['admin_collection']

SECRET_KEY = 'CDNZNO4T37HWCBP7OTOAQSSW6Z7UITFY'

# ---->>> admin<<<-----#
@app.route('/login', methods=['GET', 'POST'],subdomain="admin")
def admin_login():                                                     # Done
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        password = request.form.get('password')
        v2fa = request.form.get("2fa")
        
        # Check if the admin exists in the database
        admin = admin_collection.find_one({"admin_id": admin_id})

        if admin and admin['password'] == password:
            totp = pyotp.TOTP(SECRET_KEY)
            if totp.verify(v2fa):
                # Successful login
                session['admin_id'] = admin_id
                return jsonify({"status": "success", "message": "Login successful", "redirect_url": url_for('admin_dashboard')}), 200
            else:
                return jsonify({"status": "error", "message": "Verification Fail!"}), 401
        else:
            # Invalid credentials
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    return render_template('admin_login.html')

@app.route('/logout',subdomain="admin")
def logout():
    session.pop('admin_id', None)  # Remove user session data
    return redirect(url_for('admin_login'))

@app.route('/dashboard',subdomain="admin")
def admin_dashboard():                                                 # Done
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html')

@app.route('/add_vendor', methods=['GET', 'POST'],subdomain="admin")
def add_vendor():                                                      # Done
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        vendor_name = request.form.get('vendor_name')
        owner_name = request.form.get("owner_name")
        mobileNumber = request.form.get('mobileNumber')
        email = request.form.get('email')
        Aadhar_card = request.form.get('Aadhar_card')
        pan_card = request.form.get("pan_card")
        accountnumber = request.form.get("accountnumber")
        ifsc = request.form.get("ifsc")
        upi = request.form.get("upi")
        location = request.form.get('location')
        license_key = request.form.get('license_key')
        
        

        # Check if the vendor already exists
        if vendor_collection.find_one({"vendor_name": vendor_name}):
            return jsonify({"status": "error", "message": "Vendor already exists."}), 400
        else:
            # Add the new vendor to the database
            licenses = vendor_db["licenses"]
            vendor_collection.insert_one({
                "vendor_name": str(vendor_name).replace(" ","").lower(),
                "owner_name" :owner_name,
                "_id":mobileNumber,
                "email":email,
                "Aadhar card":Aadhar_card,
                "Pan Card":pan_card,
                "Account Number":accountnumber,
                "IFSC":ifsc,
                'UPI':upi,
                "location": location,
                "license_key": license_key,
                
            })
            license_document = {
                "_id": license_key,
                "vendor_name": str(vendor_name).replace(" ","").lower(),
                "machine_id": None,
                "registered": False,
                "creation_date": datetime.utcnow().replace(tzinfo=pytz.utc),
                "expiry_date": datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=365)
            }
            licenses.insert_one(license_document)
            return jsonify({"status": "success", "message": "Vendor added successfully."}), 200

    return render_template('add_vendor.html')

@app.route('/add_organisation', methods=['GET','POST'],subdomain="admin")
def add_organisation():                                                # Done
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        organisation_name = request.form.get('organisation_name')
        admin_name = request.form.get("admin_name")
        mobile_number = request.form.get('mobileNumber')
        location = request.form.get('location')
        aadhar_card = request.form.get('Aadhar_card')
        email = request.form.get('email')
        user_limit = request.form.get('user_limit')
        license_key = request.form.get('license_key')
        
        organisation_name = str(organisation_name).replace(" ","").lower()
        organisation_collection = organisation_db[organisation_name]

        if organisation_admin_collection.find_one({"organisation_name": organisation_name}):
            return jsonify({"status": "error", "message": "Oraganisation already exists."}), 400
        if organisation_admin_collection.find_one({"license_key": license_key}):
            return jsonify({"status": "error", "message": "Invalid license_key!"}), 400
        else:
            licenses = organisation_db["licenses"]
            organisation_collection.insert_one({
                "_id":admin_name,
                "password":str(organisation_name)+str(mobile_number)[:4]
                })
            
            organisation_admin_collection.insert_one({
                "organisation_name": organisation_name,
                "password":str(organisation_name)+str(mobile_number)[:4],
                "admin_name": admin_name,
                "_id":mobile_number,
                "email":email,
                "Aadhar_card":aadhar_card,
                "location": location,
                "user_limit":user_limit,
                "license_key": license_key,
            })
            license_document = {
                "organisation_name": str(organisation_name).replace(" ","").lower(),
                "_id": license_key,
                "machine_id": None,
                "registered": False,
                "creation_date": datetime.utcnow().replace(tzinfo=pytz.utc),
                "expiry_date": datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=365)
            }
            licenses.insert_one(license_document)
            return jsonify({"status": "success", "message": "Organisation added successfully."}), 200
    return render_template('add_vendor.html')

@app.route('/generate_key', methods=['POST'],subdomain="admin")
def generate_key():                                                    # Done
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))    
    licenses = vendor_db["licenses"]
    flag = True
    while flag:
        
        uuid_value = generate_random_key()

        # Format it to XXXX-XXXX-XXXX-XXXX
        license_key = f"{uuid_value[:4].upper()}-{uuid_value[4:8].upper()}-{uuid_value[8:12].upper()}-{uuid_value[12:16].upper()}"

        if not licenses.find_one({"_id": license_key}):
            flag = False
            return jsonify({'key': license_key})
        
def serialize_object(obj):                                             # Done
    """Convert MongoDB ObjectId to string and serialize other types."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object(i) for i in obj]
    return obj    

@app.route('/search', methods=['POST'],subdomain="admin")
def search_vendor_organisation():                                      # Done
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))    
    
    data = request.get_json()
    search_type = data.get('searchType')
    search_term = data.get('searchTerm')
    if search_type == 'vendor':
        results = vendor_collection.find({"_id":search_term})
    elif search_type == 'organisation':
        results = organisation_admin_collection.find({"_id": search_term})
    else:
        return jsonify({"status": "error", "message": "Invalid search type"}), 400

    result_list = [serialize_object(result) for result in results]
    if result_list:
        return jsonify({"status": "success", "data": result_list}), 200
    else:
        return jsonify({"status": "error", "message": " Record Not Found!"}), 400


# def delete_old_records_from_all_collections(db):

#     current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
#     thirty_minutes = timedelta(minutes=15)
#     threshold_time = current_time - thirty_minutes
#     collections = db.list_collection_names()

#     for collection_name in collections:
#         collection = db[collection_name]
        
#         records_to_delete = collection.find({
#             'upload_time': {
#                 '$lt': threshold_time}})
#         for record in records_to_delete:
#             result = collection.delete_one({'_id': record['_id']})

            
#---------------------------------------------------------------------------------------#
if __name__ == '__main__':
    #delete_old_records_from_all_collections(pdf_db)
     
    app.run(host="0.0.0.0", debug=True,port=5000)


