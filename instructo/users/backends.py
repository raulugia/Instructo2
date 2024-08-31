from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

#All the code in this file was written without assistance

#custom authentication backend so users sign in with email instead of username

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            #get user by email
            user = UserModel.objects.get(email=email)

            #check if password matches
            if user.check_password(password):
                #password matched - return user
                return user
        #case user is not found - return none        
        except UserModel.DoesNotExist:
            return None
        return None
    
    #fetch user by id -  session management
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            #retrieve user if it exists
            return UserModel.objects.get(pk=user_id)
        #case user is not found - return none   
        except UserModel.DoesNotExist:
            return None
