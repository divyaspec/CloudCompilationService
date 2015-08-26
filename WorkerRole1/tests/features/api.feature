Feature: API testing

	Scenario: Retrieve the API version
	Given I visit the homepage
	Then I can see v1 in JSON reponse 

	Scenario: Successful User creation
	Given I know the path for creating user
	When I post a json request with both username and password fields are not empty
	Then I should receive a json response containing that user's id and username
	And I can see a message created