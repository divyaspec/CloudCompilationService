from lettuce import *
from nose.tools import assert_equal, assert_in
from webtest import TestApp
from main import app

path="/api/users"
@step('I visit the homepage')
def i_visit_the_homepage(step):
    #assert True, 'This has been implented'
    world.browser = TestApp(app)
    world.response = world.browser.get('/')
    assert_equal(world.response.status_code, 200)

@step('I can see v1 in JSON reponse')
def i_can_see_v1_in_json_reponse(step):
    world.response.json == {'API_Version':'V1', 'message':'welcome to our ApI for file Upload'}

@step('I know the path for creating user')
def i_know_the_base_path_for_creating_user(step):
    path = "/api/users"

@step(u'I post a json request with both username and password fields are not empty')
def i_post_a_json_request(step):
    world.response = world.browser.post_json(path, dict(username='tom', password='secretPwd'))
    assert_equal(world.response.status_code, 200)
    

@step("I should receive a json response containing that user's id and username")
def i_received_a_json_response(step):
    user = world.response.json['user']
    'tom' in user.values() and user['id'] > 0

@step('I can see a message created')
def i_can_see_a_message_created(step):
    assert_equal(world.response.json['message'], 'created')