
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.response import Response
from oebl_irs_workflow.tests.utilities import create_and_login_user
from oebl_irs_workflow.models import Author, EditTypes, Editor, IrsUser, IssueLemma
from oebl_editor.models import LemmaArticle
from oebl_editor.tests.utilitites.db_content import create_article, create_and_assign_article


class TestSuperUser(APITestCase):

    user: User
    article: LemmaArticle

    def setUp(self):
        user = create_and_login_user(IrsUser, client=self.client)
        self.user = user
        self.article = create_article()


    def test_get_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{self.article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.WRITE, ], 'Super users have write access to all content.')



class TestEditor(APITestCase):

    user: User
    assigned_article: LemmaArticle
    not_assigned_article: LemmaArticle

    def setUp(self):
        user = create_and_login_user(Editor, client=self.client)
        self.user = user
        self.assigned_article = create_and_assign_article(user=user)
        self.not_assigned_article = create_article()

    def test_get_assigned_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{self.assigned_article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.WRITE, ], 'Editors have write access to assigned content.')

    
    def test_get_not_assigned_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{self.not_assigned_article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [], 'Editors do not have access to not assigned content.')


class TestAuthor(APITestCase):

    user: User

    def setUp(self):
        user = create_and_login_user(Author, client=self.client)
        self.user = user
    
    def test_get_not_assigned_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{create_article().pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [], 'Authors do not have access to not assigned content.')


    def test_get_view_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{create_and_assign_article(self.user, EditTypes.VIEW).pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.VIEW, ], 'Author should retrieve assigned edit type.')

    def test_get_comment_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{create_and_assign_article(self.user, EditTypes.COMMENT).pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.COMMENT, ], 'Author should retrieve assigned edit type.')


    def test_get_view_annotate_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{create_and_assign_article(self.user, EditTypes.ANNOTATE).pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.ANNOTATE, ], 'Author should retrieve assigned edit type.')

    
    def test_get_write_edit_type(self):
        response: Response = self.client.get(f'/workflow/api/v1/own-issue-lemma-assignment/{create_and_assign_article(self.user, EditTypes.WRITE).pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('edit_types', data)
        self.assertEqual(data.get('edit_types'), [EditTypes.WRITE, ], 'Author should retrieve assigned edit type.')


class TestSchema(APITestCase):

    schemas: dict

    def setUp(self):
        response: Response = self.client.get('/apis/swagger/schema/', HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK, f'Set up has failed with status code {response.status_code}'
        assert response['Content-Type'] == 'application/json', f"Set up has failed with wrong content type {response['Content-Type']}"
        schema = response.json()
        self.schemas: dict = schema['components']['schemas']

    def test_schema_is_correct(self):
        """
        It is important the the generated schema provides the right information for the frontend to build it's models/types.

        I decided against self.assertDictEqual and instead for this long manual check, so unneeded properties do not lead to failure and wrong data can be spotted very specfic and therefore fast.
        """
        schema = self.schemas.get('IssueLemmaUserAssignment')
        self.assertIsNotNone(schema, 'A model of user assignments should be provided for the frontend.')
        self.assertEqual(schema.get('type'), 'object', 'The schema should return an object.')
        properties: dict = schema.get('properties')
        self.assertIsNotNone(properties, 'The schema should define properties.')
        edit_types: dict = properties.get('edit_types')
        self.assertIsNotNone(edit_types, 'The schema should define the edit type property.')
        self.assertEqual(edit_types.get('type'), 'array', 'Edit types should be an array.')
        self.assertEqual(edit_types.get('readOnly'), True, 'edit_types should be read only.')
        items = edit_types.get('items')
        self.assertIsNotNone(items, 'Items should be defined for edit_types.')
        ref = items.get('$ref')
        self.assertIsNotNone(ref, '$ref should be defined for edit_type items.')
        self.assertEqual(ref, '#/components/schemas/EditTypesEnum', 'Edit types items should reference a list of EditTypeEnums.')
