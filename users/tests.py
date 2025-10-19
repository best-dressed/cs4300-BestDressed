from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# http redirect codes
FOUND = 302
OK = 200

testusername = "testusername"
testpassword = "testpassword123"

# This user should not be created. It is used to represent somebody that is not in the database
fakeusername = "fakeuser"
fakepassword = "fakepassword123"

def create_signup_request(username,password1,password2=None) :
    """Creates a signup request"""
    # Make the signin request correct by default
    if password2 == None :
        password2 = password1 
    
    return  {'username': username, 
             'password1': password1, 
             'password2': password2}

def create_login_request(username,password) :
    return {'username': username, 'password': password}

def create_user (username=testusername,password=testpassword) :
    return User.objects.create_user(username=testusername,password=testpassword)

def is_logged_in(client) :
    response = client.get('/')
    return response.wsgi_request.user.is_authenticated

# Create your tests here.
class LogoutTest(TestCase):
    def test_logout(self) :
        # Login client (done manually to make the tests not dependent on one another)
        create_user()
        self.client.login(username=testusername,password=testpassword)

        # check if the user is logged in
        self.assertTrue(is_logged_in(self.client))

        # log out
        response = self.client.get(reverse('logout'))

        # Check if user is logged out after logout
        self.assertFalse(is_logged_in(self.client))

class LoginTest(TestCase) :
    def setUp(self) :
        self.url = reverse("login")
    def test_login(self) :
        """tests a successful login request"""
        create_user()
        # test login with post to login
        response = self.client.post(self.url,create_login_request(testusername,testpassword))
        
        # check for redirect code after login
        self.assertEqual(response.status_code, FOUND)
        
        # check if I am logged in
        self.assertTrue(is_logged_in(self.client))

    def test_login_to_non_existant_user(self) :
        """tests a bad login request"""
        # post bad login request
        response = self.client.post(self.url,create_login_request(fakeusername,fakepassword))
        
        # Check for OK status code, which is what is usually returned on inccorect login
        self.assertEqual(response.status_code, OK)

        # check that I am not logged in
        self.assertFalse(is_logged_in(self.client))

class SignUpTest(TestCase) : 
    def sign_up(self,username=testusername,password1=testpassword,password2=testpassword) :
        signup_url = reverse("signup") 
        return self.client.post(signup_url,create_signup_request(username,password1,password2))

    def bad_signup_request_contains(self,password1,correct_contains,*,
                                    correct_response_code=OK,password2=None,
                                    username=testusername):
        """Inserts a bad password request constructed from password1 and password two, 
        checks response code and makes sure response contains the right test"""
        # make password 2 a correct response
        if (password2 == None) :
            password2 = password1
        # try to sign up 
        response = self.sign_up(username,password1,password2)
        # test response
        self.assertEqual(response.status_code,correct_response_code)
        # test the contains
        self.assertContains(response,correct_contains)



    def test_sign_up(self) :
        """Try a correct sign up, and then login to see if you are logged in"""
        # sign up
        response = self.sign_up()
        # Check if signup worked 
        self.assertEqual(response.status_code,FOUND)

        # login to account
        login_url = reverse("login")
        self.client.login(username=testusername,password=testpassword)
        self.assertTrue(is_logged_in(self.client))


    def test_sign_up_twice(self) :
        """Tests to see if signing up twice fails""" 
        # Sign up the first time
        response = self.sign_up()
        # Check if signup worked 
        self.assertEqual(response.status_code,FOUND)
        
        # try to create another client with same name
        response = self.sign_up()
        self.assertEqual(response.status_code,OK)
        # Should display that username already exists
        self.assertContains(response,"A user with that username already exists.")

    def test_sign_up_wrong_password(self) :
        """Try to sign up when two passwords differ from one another"""
        self.bad_signup_request_contains("orange123",
                                         "The two password fields didn’t match.",
                                         password2="banana123")

    def test_sign_up_short_password(self) :
        self.bad_signup_request_contains("abc123",
            "This password is too short. It must contain at least 8 characters.")
    
    def test_sign_up_common_password(self) :
        """User should fail if signup password is too common"""
        self.bad_signup_request_contains("password",
                                         "This password is too common.")
    
    def test_sign_up_username_same_as_password(self):
        """Signup should fail if password is too similar to username"""
        self.bad_signup_request_contains(testpassword,
                                         "The password is too similar to the username.",
                                         username=testpassword)

        




        

        

