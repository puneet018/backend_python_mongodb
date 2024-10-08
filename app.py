from flask import Flask, request, Response, session, jsonify, make_response, url_for, send_file
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo , pymongo
from twilio.rest import Client
import json, random
from bson import ObjectId
from configparser import ConfigParser
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
# from flask_session import Session
import os
from bson import json_util
# import jwt
# from flask_sqlalchemy import SQLAlchemy
# from functools import wraps
# from google.cloud import storage
import gridfs
import base64
import io

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.secret_key = 'mynameisnick'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
# app.config["MONGO_URI"] = "mongodb+srv://nikkyvishwa90:nikkyvishwa90@cluster0.jc8u7cz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/sample_mflix"
# db = PyMongo(app).db
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# DATABASE connection
client = pymongo.MongoClient('mongodb+srv://shivams:shivams@cluster0.jc8u7cz.mongodb.net/sample_mflix?retryWrites=true&w=majority&appName=Cluster0')
userdb = client['FlaskDB']
users = userdb.users
properties = userdb.properties
# properties = userdb.properties
fs = gridfs.GridFS(userdb)

otp_status = ''

# # Set the environment variable to point to your service account key file
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-file.json"

# # Initialize a Cloud Storage client
# client = storage.Client()


# Custom JSON Encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# decorator for verifying the JWT
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         # jwt is passed in the request header
#         if 'x-access-token' in request.headers:
#             token = request.headers['x-access-token']
#         # return 401 if token is not passed
#         if not token:
#             return jsonify({'message' : 'Token is missing !!'}), 401
  
#         try:
#             # decoding the payload to fetch the stored details
#             data = jwt.decode(token, app.config['SECRET_KEY'])
#             current_user = User.query\
#                 .filter_by(public_id = data['public_id'])\
#                 .first()
#         except:
#             return jsonify({
#                 'message' : 'Token is invalid !!'
#             }), 401
#         # returns the current logged in users context to the routes
#         return  f(current_user, *args, **kwargs)
  
#     return decorated


# Route to get all users
@app.route('/users', methods=['GET', 'POST'])
def get_users():
	user_data = users.find()
	return user_data

@app.route('/insert', methods=['POST', 'GET'])
@cross_origin()
def insert_data():
    
		data = request.get_json()
		# if name != '':
		_id = users.insert_one(data)
		print(_id.inserted_id)
		return 'true'
		# else:
		# 	return "False"

def check_user():
	if request.method == 'POST':
		user = request.get_json()
		user_data = users.find_one(user)
		if user_data == None:
			return False, ""
		else:
			return True, user_data["name"]


# OTP authentication confrigration
# twilio setting
config = ConfigParser()
config.read('config.ini')
auth_token = config.get('auth', 'token')
account_sid = config.get('auth', 'account_sid')
verify_sid = config.get('auth', 'verify_sid')
from_number = config.get('auth', 'from_number')
client = Client(account_sid,auth_token)

# create a new user
@app.route('/create_user', methods=['POST'])
def create_user():
	new_user = request.get_json()
	find_user = users.find_one({"mobile_number":new_user['mobile_number']})
	mobile_number = new_user['mobile_number']
	# full_name = new_user['full_name']
	print(find_user)
	if find_user == None:
		# new user insert
		_id = users.insert_one(new_user)
	else:
		return jsonify({'status_code':200,'message':'already registered'})
	# sending opt for verification of user
	# status  = send_otp_via_sms(mobile_number)
	return jsonify({'status_code':200,'message':'done'})

# Create New Users when it will come from direct with login
def create_login_user(mobile_number):
	new_user = request.get_json()
	new_user['mobile_number'] = mobile_number
	# full_name = new_user['full_name']
	# new user insert
	_id = users.insert_one(new_user)
	# else:
		# old user forward to login
	# sending opt for verification of user
	status  = send_otp_via_sms(mobile_number)
	return status

# login user with otp
@app.route('/login_user', methods=['POST'])
def login_user():
	status = jsonify({})
	user = request.get_json()
	mobile_number = user['mobile_number']
	find_user = users.find_one({"mobile_number":mobile_number})
	
	if find_user == None:
		status = create_login_user(mobile_number)
	else:
		status = send_otp_via_sms(mobile_number)
		# ['new_user_code']='100'
		
	# sending opt for verification of user
	# status = send_otp_via_sms(mobile_number)
	# if otp_status == 'approved':
	# find_user = users.find_one(mobile_number)
	
	return status

@app.route('/login_user_manual', methods=['POST'])
def login_user_manual():
	app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
	print(session.permanent)
	user = request.get_json()
	email = user['email']
	password = user['password']
	find_user = users.find_one({"email":email})
	if find_user == None:
		return jsonify({'status_code':404,'message':'Please create account first'})
	else:
		if find_user['password'] == password:
			find_user['status_code'] = 200
			session['logged_in']=True
			find_user['session'] = True
			return JSONEncoder().encode(find_user)
		else:
			return jsonify({'status_code':500,'message':'Password is not correct'})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return jsonify({'status_code':500,'message':'Logout Done','session':False})

# Define the global variable
g_code = 0
g_mobile_number = None
g_new_user_vi_number = 0

# send otp to user number
def send_otp_via_sms(mobile_number):
	session.permanent = True
	# response.html.render(send_cookies_session=True)
	# global g_code
	# global g_mobile_number
	code = random.randint(100000, 999999)
	session['code'] = 121212
	# g_code = 121212
	session['mobile_number'] = mobile_number
	# g_mobile_number = mobile_number
	# app.logger.info(f'Session set: {session["code"]}')
	# message = client.messages.create(body=f"Hello Dear User Your one-time password is "+str(code), from_=from_number,  to=mobile_number)
	# otp_verification = client.verify.services(verify_sid).verifications.create(
	#  to = mobile_number, channel="sms")npm install -g firebase-tools
	# print(str(session.get('code'))+str('-------send_otp_via_sms-------'))
	return jsonify({'status_code':200,'message':'message.status'})

# def set_cookie():
#     # resp = make_response("Setting a cookie!")
#     # resp.set_cookie('SecureCookieSession',{'_permanent': True, 'code': code, 'mobile_number': mobile_number})
# 	cookies = {'session': '17ab96bd8ffbe8ca58a78657a918558'}
# 	request_set = request.post('backend-python-mongodb.onrender.com', cookies=cookies)
# 	return request_set

# Check OTP
@app.route('/check_otp', methods=['POST'])
def check_otp():
	# global g_code, g_mobile_number
	verify_data = request.get_json()
	try:
		# set_cookie()
		print(request.cookies.get('session'))
		# print(session)
		# if session.get('code') != None:
		if 'code' in session.keys():
				# temp = int(verify_data['otp_code'])
			if session.get('code') == int(verify_data['otp_code']):
				# otp_status = "approved"
				data = users.find_one({"mobile_number":session.get('mobile_number')})
				print(data)
				if data and 'email' in data:
					data['is_new_user'] = 'no'
				else:
					data['is_new_user'] = 'yes'
				# Serialize the document using the custom encoder
				# data = json.dumps(data, cls=JSONEncoder)
				session.pop('code', None)
				session['logged_in']=True
				data['session'] = True
				# g_mobile_number = None
				# g_code = 0
			else:
				return jsonify({'status_code':500, 'message' : "wrong please resend OTP"})
		else:
			return jsonify({'status_code':500, 'message' : "Session is expire please resend otp", 'session' : False})
	except (BaseException) as e:
		return jsonify({"status_code": 500, "message": str(e)})
	data['status_code'] = 200
	
	return JSONEncoder().encode(data)

# Save user details in DB
@app.route('/save_user_details', methods=['POST'])
def save_user_details():
	new_user_details = request.get_json()
	object_id = new_user_details['_id']
	# Values to be updated.
	new_user_values = { "$set": { 'full_name':new_user_details['full_name'], 'email': new_user_details['email'] } }
	users.update_one({'_id': object_id},new_user_values)
	return jsonify({'status_code':200,'message':'updated'})



# Store property data 
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# real-estate-images-storage@real-estate-management-0011.iam.gserviceaccount.com
@app.route('/property_save', methods=['POST'])
def property_save():
	print('===============In Property save Multi================')
	property_data = request.form.get('json')
	file_ids = []
	if property_data:
		property_data = json.loads(property_data) # parse the JSON string
		try:
			# Access file data
			# file = request.files['file']
			files = request.files.getlist('file')
			print(files,'================ if out')
			if 'files' in request.files:
				print(files,"============")
				for file in files:
					if file.filename == '':
						property_image_name = secure_filename(file.filename)
						file_id = fs.put(file, filename=property_image_name, content_type = file.content_type)
						file_ids.append(file_id)
				property_data['propertyImagesId'] = file_ids
				_id = properties.insert_one(property_data)
				response_data = jsonify({'status': 200, 'status_msg': 'Data saved'})
			else:
				response_data = jsonify({'status': 200, 'status_msg': 'Image is not save', 'data': property_data})

		except (BaseException) as e:
			response_data = jsonify({"status": 404, "message": str(e)})
		return response_data
	else:
		return jsonify({"status": 404, "message":"data not available"})

# # Store property data 
# APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# # real-estate-images-storage@real-estate-management-0011.iam.gserviceaccount.com
# @app.route('/property_save', methods=['POST'])
# def property_save():
# 	print('===============In Property save================')
# 	property_data = request.form.get('json')
# 	if property_data:
# 		property_data = json.loads(property_data) # parse the JSON string
# 		try:
# 			# Access file data
# 			file = request.files['file']
# 			if 'file' in request.files:
# 				property_image_name = secure_filename(file.filename)
# 				file_id = fs.put(file, filename=property_image_name, content_type = file.content_type)
# 				property_data['propertyImagesId'] = file_id
# 				_id = properties.insert_one(property_data)
# 				response_data = jsonify({'status': 200, 'status_msg': 'Data saved'})
# 			else:
# 				response_data = jsonify({'status': 200, 'status_msg': 'Image is not save', 'data': property_data})

# 		except (BaseException) as e:
# 			response_data = jsonify({"status": 404, "message": str(e)})
# 		return response_data
# 	else:
# 		return jsonify({"status": 404, "message":"data not available"})



# def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
#     """Uploads a file to the bucket."""
#     # bucket_name = "your-bucket-name"
#     # source_file_name = "local/path/to/file"
#     # destination_blob_name = "storage-object-name"

#     bucket = client.bucket(bucket_name)
#     blob = bucket.blob(destination_blob_name)

#     blob.upload_from_filename(source_file_name)

#     print(f"File {source_file_name} uploaded to {destination_blob_name}.")


# Get properties data 
@app.route('/properties_get', methods=['GET'])
def properties_get():
	
	# try:
		properties_data = JSONEncoder().encode([prop for prop in properties.find({})])
		jdata = json.loads(properties_data)
		for pd in jdata: 
			json_data = properties.find_one({'_id': json_util.ObjectId(pd["_id"])})
			
			file = fs.get(json_data['propertyImagesId'])
			file_content = file.read()
			file_base64 = base64.b64encode(file_content).decode('utf-8')
			pd['image_file'] = file_base64
			pd['imgage_content_type'] = file.content_type
			pd['file_name'] = file.filename
		print(jdata,"==========------------------------------------------==")

		#  response_data = {
        #     "filename": file_data['filename'],
        #     "content_type": file_data['content_type'],
        #     "file": file_base64,  # Base64 encoded image
        #     "additional_data": {
        #         # Include any other relevant data
        #         "description": file_data.get('description', 'No description'),
        #         "uploaded_at": file_data.get('uploaded_at', 'Unknown'),
        #     }
        # }
		return jsonify({'status': 200, 'data': jdata})
	# except (BaseException) as e:
	 	# return jsonify({"status": 404, "message": str(e)})

# Get properties data 
@app.route('/properties_get/<int:property_id>', methods=['GET'])
def property_get(property_id):
	try:
		response_data = jsonify({'status': 200, 'data': properties.find_one(property_id)})
	except (BaseException) as e:
		response_data = jsonify({"status": 404, "message": str(e)})
	return response_data

# Delete Properties data 
@app.route('/property_delete/<int:property_id>', methods=['GET'])
def property_delete(property_id):
	try:
		response_data = jsonify({'status': 200, 'data': properties.delete_one(property_id)})
	except (BaseException) as e:
		response_data = jsonify({"status": 404, "message": str(e)})
	return response_data

# Delete many Properties data 
# @app.route('/properties_delete/<int:property_id>', methods=['GET'])
# def property_get():
# 	property_data_ids = request.get_json()
# 	try:
# 		response_data = jsonify({'status': 200, 'data': properties.delete_many(property_data_ids)})
# 	except (BaseException) as e:
# 		response_data = jsonify({"status": 404, "message": str(e)})
# 	return response_data
# Route to update a user by ID

@app.route('/property_update/<int:propertyId>', methods=['PUT'])
def property_update(propertyId):
    property = next((p for p in properties if p['id'] == propertyId), None)
	# print(property)	
    if property:
        updates = request.get_json()
        property.update(updates)
        return jsonify(property)
    else:
        return jsonify({'error': 'User not found'}), 404

# Route to get a user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in data if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404

# Route to update a user by ID
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = next((u for u in data if u['id'] == user_id), None)
    if user:
        updates = request.get_json()
        user.update(updates)
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404

# # Route to delete a user by ID
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    global data
    data = [u for u in data if u['id'] != user_id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)



