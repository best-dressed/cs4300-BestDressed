from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

testusername = "testusername"
testpassword = "testpassword123"

# This user should not be created. It is used to represent somebody that is not in the database
fakeuser = "fakeuser"
fakepassword = "fakepassword123"

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
    def test_login(self) :
        create_user()

