import keyring
import getpass

class CredentialManager():
    def __init__(self):
        pass
    def set_credentials(self):
        username = input('Username: ')
        keyring.set_password('plenty-identity', 'user', username)
        keyring.set_password('plenty-identity', 'password', getpass.getpass())

    def get_credentials(self):
        user = keyring.get_password('plenty-identity', 'user')
        password = keyring.get_password('plenty-identity', 'password')
        if not user or not password:
            return {}
        return {'username':user, 'password':password}

    def delete_credentials(self):
        keyring.delete_password('plenty-identity', 'user')
        keyring.delete_password('plenty-identity', 'password')
