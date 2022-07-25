

from typing import Type, Union
from django.test import Client


from oebl_irs_workflow.models import Author, Editor, IrsUser, User


def create_user(
        UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']],
    username: str,
    password: str,
) -> Union['Editor', 'IrsUser', 'Author']:
    user: 'User'
    if UserModel is IrsUser:
        user = IrsUser.objects.create_superuser(username=username)
    else:
        user = UserModel.objects.create(username=username)

    user.set_password(password)
    user.save()
    return user


def create_and_login_user(UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']], client: 'Client') -> Union['Editor', 'IrsUser', 'Author']:
        username = UserModel.__class__.__name__
        password = 'password'
        user = create_user(
            UserModel, username=username, password=password)
        client.login(username=username, password=password)
        return user


class SetUpUserMixin:

    user: Union['Editor', 'IrsUser', 'Author']
    client: 'Client'

    def setUpUser(self):
        UserModel = self.__annotations__['user']
        self.user = create_and_login_user(UserModel, self.client)
        return self.user