from flask import Flask, request, Response, session, jsonify
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo , pymongo
from twilio.rest import Client
import json
from bson import ObjectId
from configparser import ConfigParser
# from jsonify import convert
import os

app = Flask(__name__)

app.secret_key = b'NjYgNmMgNjEgNzMgNmIgNjMgNmYgNjQgNjU='
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
# account_sid = os.getenv("TWILIO_ACCOUNT_SID")
# auth_token = os.getenv("TWILIO_AUTH_TOKEN")
# verify_sid = os.getenv("VERIFY_SID")
# from_number = os.getenv("TWILIO_NUMBER")

account_sid = "ACe153842b9f2450d2a72c5f7386220822"
verify_sid = "f7f8e9eac96a31ff711866808e29d3a9"
from_number = "+15706825138"

config = ConfigParser()
config.read('config.ini')
auth_token = config.get('auth', 'token')
print(auth_token)
client = Client(account_sid,auth_token)

# Route to create a new user
@app.route('/create_user', methods=['POST'])
def create_user():

	new_user = request.get_json()
	find_user = users.find_one({"mobile_number":new_user['mobile_number']})
	mobile_number = new_user['mobile_number']
	userName = new_user['name']
	print(find_user)
	if find_user == None:
		# new user insert
		_id = users.insert_one(new_user)
	# else:
		# old user forward to login
	# sending opt for verification of user
	status  = send_otp_via_sms(mobile_number)
	return 'status'

@app.route('/login_user', methods=['POST'])
def login_user():
	user = request.get_json()
	mobile_number = user['mobile_number']
	# sending opt for verification of user
	status = send_otp_via_sms(mobile_number)
	# if otp_status == 'approved':
	# find_user = users.find_one(mobile_number)
	return status

def send_otp_via_sms(mobile_number):
	code = 123012
	session['code'] = code
	massage = client.messages.create(body=f"Hello Dear User Your one-time password is "+str(code), from_=from_number,  to=mobile_number)
	# otp_verification = client.verify.services(verify_sid).verifications.create(
	#  to = mobile_number, channel="sms")
	session['mobile_number'] = mobile_number
	return massage.status


# Sample MongoDB document with ObjectId

@app.route('/check_otp', methods=['POST'])
def check_otp():
	verify_data = request.get_json()
	if session['code'] == int(verify_data['otp_code']):
		# otp_status = "approved"
		print(session['mobile_number'])
		data = users.find_one({"mobile_number":session['mobile_number']})
		print(data)
				# Serialize the document using the custom encoder
		data = json.dumps(data, cls=JSONEncoder)
		print(data)
		session['code']=None
	else:
		data = "not approved"
	# otp_check = client.verify.services(verify_sid).verification_checks.create(
	# 	to=session['mobile_number'], code=verify_data['otp_code']
	# )
	# otp_status = otp_check.status

	return jsonify(data)

@app.route('/property_save', methods=['POST'])
def property_save():
	property_data = request.get_json()
	_id = properties.insert_one(property_data)
	return 


# Route to get a user by ID
# @app.route('/users/<int:user_id>', methods=['GET'])
# def get_user(user_id):
#     user = next((u for u in data if u['id'] == user_id), None)
#     if user:
#         return jsonify(user)
#     else:
#         return jsonify({'error': 'User not found'}), 404


# # Route to update a user by ID
# @app.route('/users/<int:user_id>', methods=['PUT'])
# def update_user(user_id):
#     user = next((u for u in data if u['id'] == user_id), None)
#     if user:
#         updates = request.get_json()
#         user.update(updates)
#         return jsonify(user)
#     else:
#         return jsonify({'error': 'User not found'}), 404

# # Route to delete a user by ID
# @app.route('/users/<int:user_id>', methods=['DELETE'])
# def delete_user(user_id):
#     global data
#     data = [u for u in data if u['id'] != user_id]
#     return '', 204

if __name__ == '__main__':
    app.run(debug=True)



