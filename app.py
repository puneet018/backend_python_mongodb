from flask import Flask, request, Response, session, jsonify, make_response
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo , pymongo
from twilio.rest import Client
import json, random
from bson import ObjectId
from configparser import ConfigParser
from datetime import timedelta
import os



app = Flask(__name__)

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

otp_status = ''


# Custom JSON Encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


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
		# status.set_data('{"new_user_code":100}')
	else:
		status = send_otp_via_sms(mobile_number)
		# ['new_user_code']='100'
		
	print(status)
	# sending opt for verification of user
	# status = send_otp_via_sms(mobile_number)
	# if otp_status == 'approved':
	# find_user = users.find_one(mobile_number)
	
	return status

@app.route('/login_user_manual', methods=['POST'])
def login_user_manual():
	app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
	print(session.permanent)
	user = request.get_json()
	email = user['email']
	password = user['password']
	find_user = users.find_one({"email":email})
	if find_user == None:
		return jsonify({'status_code':404,'message':'Please create account first'})
	else:
		if find_user['password'] == password:
			return JSONEncoder().encode(find_user), 200
		else:
			return jsonify({'status_code':500,'message':'Password is not correct'})

# Define the global variable
g_code = 0
g_mobile_number = None

# send otp to user number
def send_otp_via_sms(mobile_number):
	# session.permanent = True
	global g_code
	global g_mobile_number
	code = random.randint(100000, 999999)
	# session['code'] = 121212
	g_code = 121212
	# session['mobile_number'] = mobile_number
	g_mobile_number = mobile_number
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




# check OTP
@app.route('/check_otp', methods=['POST'])
def check_otp():
	global g_code, g_mobile_number
	verify_data = request.get_json()
	try:
		# set_cookie()
		# print(request.cookies.get('session'))
		# print(session)
		# if session.get('code') != None:
		# temp = int(verify_data['otp_code'])
		if g_code == int(verify_data['otp_code']):
			# otp_status = "approved"
			data = users.find_one({"mobile_number":g_mobile_number})
			# Serialize the document using the custom encoder
			# data = json.dumps(data, cls=JSONEncoder)
			# session.pop('code', None)
			g_mobile_number = None
			g_code = 0
		else:
			return jsonify({'status_code':500, 'message' : "wrong please resend OTP"})
		# else:
		# 	return jsonify({'status_code':500, 'message' : "Session is expire please resend otp"})
	except (BaseException) as e:
		return jsonify({"status_code": 500, "message": str(e)})
	data['status_code'] = 200
	return JSONEncoder().encode(data)


# check_otp()
# Store property data 
@app.route('/property_save', methods=['POST'])
def property_save():
	property_data = request.get_json()
# 	property_data = {
#     "address": "address1",
#     "description": "longText",
#     "name": "Homemaker Grande A",
#     "type": PropertyType.residential,
#     "position": {
#       "lat": 8.948677279926585,
#       "lng": 125.5470567303216,
#     },
#     "price": 210000,
#     "images": "images1",
#     "updatedAt": Date(),
#     "enquiries": ['12'],
#     "currency": "PHP",
#     "features": ['Item 1', 'Item 2', 'Item 3', 'Item 4'],
#     "user_id": '01',
#   }
	try:
		_id = properties.insert_one(property_data)
		response_data = jsonify({'status': 200, 'status_msg': 'Data saved'})
	except (BaseException) as e:
		response_data = jsonify({"status": 404, "message": str(e)})
	return response_data

# Get properties data 
@app.route('/properties_get', methods=['GET'])
def properties_get():
	try:
		response_data = jsonify({'status': 200, 'data': properties.find()})
	except (BaseException) as e:
		response_data = jsonify({"status": 404, "message": str(e)})
	return response_data

# Get properties data 
@app.route('/properties_get/<int:property_id>', methods=['GET'])
def property_get(property_id):
	try:
		response_data = jsonify({'status': 200, 'data': properties.find_one(property_id)})
	except (BaseException) as e:
		response_data = jsonify({"status": 404, "message": str(e)})
	return response_data


# Route to get a user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in data if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404


# # Route to update a user by ID
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



