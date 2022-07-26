

from typing import Optional, Type, Union
from rest_framework.test import APITestCase, APIClient


from oebl_irs_workflow.models import Author, Editor, IrsUser, IssueLemma, Lemma, User
from oebl_irs_workflow.serializers import LemmaSerializer


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


def create_and_login_user(
        UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']], 
        client: 'APIClient',
        user_number: int = 1,  # to create multiple users of a type
        ) -> Union['Editor', 'IrsUser', 'Author']:
        username = f'{UserModel.__class__.__name__}-{user_number}'
        password = 'password'
        user = create_user(
            UserModel, username=username, password=password)
        client.login(username=username, password=password)
        return user


class SetUpUserMixin:

    user: Union['Editor', 'IrsUser', 'Author']
    client: 'APIClient'

    def setUpUser(self):
        UserModel = self.__annotations__['user']
        self.user = create_and_login_user(UserModel, self.client)
        return self.user


def create_valid_issue_lemma_json_for_editor(editor_id: Optional[int]) -> dict:
    lemma = Lemma.objects.create(first_name='First Name', name='Last Name')
    serializer = LemmaSerializer()
    return {
        'editor': editor_id,
        'lemma': serializer.to_representation(instance=lemma),
    }


class EditorTestCaseMixin:

    editor: 'Editor'

    def setUp(self) -> None:
        self.editor = Editor.objects.create()


class AssignedIssueLemmaMixin:

    assigned_issue_lemma: IssueLemma

    def setUp(self) -> None:
        self.assigned_issue_lemma = IssueLemma.objects.create(
            editor = Editor.objects.create(),
            lemma = Lemma.objects.create(first_name='First Name', name='Last Name'),       
        )

class NotAssignedIssueLemmaMixin:

    not_assigned_issue_lemma: IssueLemma

    def setUp(self) -> None:
        self.not_assigned_issue_lemma = IssueLemma.objects.create(
            editor = None,
            lemma = Lemma.objects.create(first_name='First Name', name='Last Name'),       
        )



class MixedIssueLemmasMixin:
    editor: 'Editor'
    assigned_issue_lemma: IssueLemma
    not_assigned_issue_lemma: IssueLemma


    def setUp(self):
        self.editor: 'Editor' = Editor.objects.create(username='Our test editor')
        self.editor.set_password('password')
        self.editor.save()
        self.assigned_issue_lemma = IssueLemma.objects.create(
            editor = self.editor,
            lemma = Lemma.objects.create(first_name='First Name', name='Last Name'),       
        )
        self.not_assigned_issue_lemma = IssueLemma.objects.create(
            editor = Editor.objects.create(username='Any editor'),
            lemma = Lemma.objects.create(first_name='First Name', name='Last Name'),       
        )


class LogOutMixin:

    def tearDown(self: 'APITestCase') -> None:
        self.client.logout()


