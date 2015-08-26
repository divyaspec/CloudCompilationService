#!/usr/bin/env python
import os, os.path

from lettuce import world
from os import environ
from flask import Flask, abort, request, jsonify, g, url_for, make_response, json
from flask.ext.autodoc import Autodoc
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from azure.storage import BlobService
from azure.servicebus import ServiceBusService, Message, Queue
from azure.storage import BlobService, QueueService
import uuid, hashlib
import logging
from applicationinsights.requests import WSGIApplication
from applicationinsights.logging import enable
from applicationinsights import TelemetryClient
tc = TelemetryClient('5d8c355c-652e-46e7-b607-2aa537924748')
tc.track_event('Test event')
tc.flush()

# initialization
app = Flask(__name__)
auto = Autodoc(app)
app.config['SECRET_KEY'] = 'uclmicrobitteam'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['DEBUG'] = True
# Container uploads
app.config['STORAGE_ACC'] = 'linuxvmstorage'
app.config['STORAGE_KEY'] = 'gW6GwPYmuBL7Gs59eEa6br/G6N09+AxChQ4EBKNIF64JyEf9KDUxPdfJxov4EUf29tndVBHcTqgLAHfSe5A/5A=='
# Azure Service Bus Queue 
app.config['SERVICE_BUS_NAMESPACE'] = 'servicebusqueue-json'
app.config['SHAREDACCESSKEYNAME'] = 'RootManageSharedAccessKey' 
app.config['SHAREDACCESSKEY'] = 'mrpW+NFfQCiRn3lRtVsyNwY7Rs3Tzh9hUMifZoZRPHU='
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['TEST_FOLDER'] = 'test/'

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
app.wsgi_app = WSGIApplication('5d8c355c-652e-46e7-b607-2aa537924748', app.wsgi_app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
@auto.doc()
def new_user():
    print "before request.json"
    print request.get_json
    if request.headers['Content-Type'] == 'application/json':
        #print "before request.json"
        if not request.json:
            abort(400)
    
    username = request.get_json('username')
    username = request.json.get('username')
    password = request.get_json('password')
    password = request.json.get('password')
    print username
    print password
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
@auto.doc()
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auto.doc()
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/api/resource')
@auto.doc()
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hi, %s!' % g.user.username})

@app.route('/api/uploads', methods=['POST'])
@auto.doc()
@auth.login_required
def file():

    """Renders the file page."""
    if request.headers['Content-Type'] == 'application/json':
       if not request.json:
        abort(400)
    jdata = json.loads(request.data)
    print jdata

    if not request.json:
        abort(400)
    jsonContent = json.dumps(request.json)
    print jsonContent
    
    #hash the filename using sha1 from hashlib library
    #this may be prefered depending wehther your want the consumer of the api to remember the guid or not
    #uni.encode
    guid_object = hashlib.sha1(jsonContent.encode('utf-8'))
    guid = guid_object.hexdigest()
    print guid
   
    
    #or generate random unique ID from uuid package
    uid = uuid.uuid4()
    print uid
   
    #guiduid= guid + uid
    #do other stuffs
    #you can also add the extension or get it from the file name or put in the message queues
    #extension = fileSRC.rsplit('.', 1)[1]
    

    #call directly create_blob_simple or create a folder to store the information (long way to go and less efficient)
    #create_blob_simple('uploads', guid + '.' + extension, fileSettings)
    create_blob_simple('uploads', guid, jsonContent)
    create_queue_simple(guid)
    #using Service Bus queues
    #create_service_bus_queue_simple(guid)
    create_service_bus_topic(guid)
    #second alternative
    #save the content in temporary file named by its uuid in upload directory
    # create directory for temporary save if not exist           
    #if not os.path.exists(app.config['UPLOAD_FOLDER']):
        #os.makedirs(app.config['UPLOAD_FOLDER'])

    #path = os.path.join(app.config['UPLOAD_FOLDER'], guid+extension)
    #with open(path,"a") as file:
        #file.write(filecontent)[
    #create_blob('uploads', guid + '.' + extension, path)
    
    return jsonify({"status_code":200, "message":"posted", 'postedJSON': request.json, "upload": "file"})
    #return jsonify({'guid':str(guid), 'message': fileJson, 'postString':request.json['filename'], 'actualContent':filecontent})


@app.route('/test')
@auto.doc()
@auth.login_required
def generate_json_test_file():
    """generate json test file to be used"""
    if not os.path.exists(app.config['TEST_FOLDER']):
        os.makedirs(app.config['TEST_FOLDER'])
    with open(os.path.join(app.config['TEST_FOLDER'], "jsonOutput.txt"), "a") as outfile:
        json.dump(fileJSON, outfile, indent=4)
    return "upload successful"

#this function will all allow you to be more efficient without creating a folder.
def create_blob_simple(container, guid, jsonContent):
    #No need to create a folder to store the file 
    #more efficient
    """ initialisation azure storage"""
    #BlobService object using the storage account name and account key
    blob_service = BlobService(account_name=app.config['STORAGE_ACC'], account_key=app.config['STORAGE_KEY'])
    
    #BlobService object to create the container "UPLOADS" if it doesn't exist
    blob_service.create_container(container)

    #make the container available to the public
    blob_service.set_container_acl(container, x_ms_blob_public_access='container')

    #store in the block
    blob_service.put_block_blob_from_text(container, guid, jsonContent)

# Using Service_bus_queue, a new queue is created with queue siz 5GB & time to live value of 1 min
def create_service_bus_queue_simple(guid):
    bus_service = ServiceBusService(
    service_namespace='servicebusqueue-json',
    shared_access_key_name='queue-listener',
    shared_access_key_value='V5raw40+X20pV0aAqymsfuwnU9S17EA6QvxYJ+nelvs=')
    #queue_options = Queue()
    #queue_options.max_size_in_megabytes = '5120'
    #queue_options.default_message_time_to_live = 'PT1M'
    #bus_service.create_queue('jsonservicebusqueue', queue_options)
    bus_service.create_queue('jsonqueue')
    msg = Message(guid)
    bus_service.send_queue_message('jsonqueue', msg)
    msg = bus_service.receive_queue_message('jsonqueue', peek_lock=False)
    print(msg.body)

def create_service_bus_topic(guid):
    bus_service = ServiceBusService(
    service_namespace='servicebusqueue-json',
    shared_access_key_name='topic-listener',
    shared_access_key_value='nDqSoNekR5wWT+RKaixPBinVPaFrTmXvgwZ2PUh6AmI=')
    bus_service.create_topic('jsonpayload-topic')
    msg = Message(guid)
    bus_service.send_topic_message('jsonpayload-topic', msg)
    print(msg.body)

# The below function is using Azure Queues to create a queue
def create_queue_simple(guid):
    """ initialisation azure queues"""
    queue_service = QueueService(account_name=app.config['STORAGE_ACC'], account_key=app.config['STORAGE_KEY'])
    queue_service.create_queue('jsonqueue')

   # To insert a message into a queue, use the put_message method to create a new msg and add it to the queue
    queue_service.put_message('jsonqueue', guid)
    messages = queue_service.get_messages('jsonqueue')
    
    print messages
    # To get the queue length 
    queue_metadata = queue_service.get_queue_metadata('jsonqueue')
    count = queue_metadata['x-ms-approximate-messages-count']

@app.route('/')
@app.route('/documentation')
def documentation():
    return auto.html()



if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    if not os.path.exists('db.sqlite'):
        db.create_all()
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)