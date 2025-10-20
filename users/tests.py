from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# http redirect codes
FOUND = 302
OK = 200
MOVED_PERMANENTLY = 301

# The username and password for a test user, not used in production, only used during testing
testusername = "testusername"
testpassword = "testpassword123"
othertestpassword = "testpassword123456"

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

def create_password_change_request(oldpassword,newpassword1,newpassword2=None) :
    # Make newpassword two be newpassword1 by default
    if newpassword2 == None :
        newpassword2 = newpassword1

    return {'old_password': oldpassword, 
            'new_password1': newpassword1,
            'new_password2': newpassword2}

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
        response = self.client.post(reverse('logout'))

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

        

class ChangePasswordTest(TestCase) : 
    def setUp(self) :
        # set the change urls
        self.changeurl = reverse("password_change")
        self.doneurl = reverse("password_change_done")
    
    def create_user_and_login(self):
        # create a user 
        self.user = create_user(testusername,testpassword) 
        # log in as the user
        self.login()

    def login(self,username=testusername,password=testpassword) :
        return self.client.post(reverse('login'),create_login_request(username,password))


    def logout(self) :
        """Logs the client out, used to test if the password changed"""
        self.client.post(reverse('logout'))


    def test_logged_in(self):
        """This test is here to catch any problems with setup, it isn't directly related to the feature"""
        self.create_user_and_login()
        self.assertTrue(is_logged_in(self.client))
    
    def test_successful_change(self) : 
        """Tests to see if password changes on successful password change"""
        # login 
        self.create_user_and_login()

        # Change password
        response = self.client.post(self.changeurl,
                                    create_password_change_request(testpassword,othertestpassword))
        
        # Make sure the password change worked
        self.assertEqual(response.status_code,FOUND)
        
        # check if users password changed
        user = User.objects.get(username=testusername)
        self.assertTrue(user.check_password(othertestpassword))

        # logout 
        self.logout()

        # try logging in with old credentials, should fail to login
        self.login(password=testpassword)
        self.assertFalse(is_logged_in(self.client))

        # Login with new credentials
        self.login(password=othertestpassword)
        self.assertTrue(is_logged_in(self.client))

    def test_not_logged_in(self) :
        """Check for redirect if we are not logged in"""
        response = self.client.post(self.changeurl,
                                    create_password_change_request(testpassword,othertestpassword))
        self.assertEqual(response.status_code,FOUND)
        # this returns a url that looks like 'login?something...' so we need to check if the thing is inside
        # of it rather than equal, check if it is in the redirect chain
        self.assertIn(reverse('login'), response['Location'])
    
    def test_wrong_password(self):
        """This tests to make sure signup fails if the password is wrong"""
        # login
        self.create_user_and_login()

        # Change password
        response = self.client.post(self.changeurl,
                                    create_password_change_request('foo1234',
                                                                    othertestpassword))
        
        # Make sure the password change failed
        self.assertEqual(response.status_code,OK)
        # see if it printed the right message
        self.assertContains(response,"Your old password was entered incorrectly. Please enter it again.")
        
        # check if users password changed
        user = User.objects.get(username=testusername)
        self.assertFalse(user.check_password(othertestpassword))

        # logout 
        self.logout()

        # try logging in with old credentials, should succeed
        self.login(password=testpassword)
        self.assertTrue(is_logged_in(self.client))
        

        

