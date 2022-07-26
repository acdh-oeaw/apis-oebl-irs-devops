"""
# Summary Of Tests Rules In This Module:

Test rules regarding the assignment of editors to IssueLemmas -> `IssueLemma.editor` 

## POST IssueLemmas With Assignments

- Super users can POST IssueLemmas assigned to an Editor.
- Editors can not POST IssueLemmas assigned to an Editor.
- Authors can not POST IssueLemmas assigned to an Editor.

## DELETE IssueLemmas With Assignments

- Super users can DELETE IssueLemmas assigned to an Editor.
- Editors can not DELETE IssueLemmas assigned to an Editor.
- Authors can not DELETE IssueLemmas assigned to an Editor.

## Unassign Editors with PATCH Or Put From IssueLemmas

- Super users can PATCH and POST IssueLemmas to unassign them from an Editor.
- Editors can not PATCH and POST IssueLemmas to unassign them from an Editor.
- Authors can not PATCH and POST IssueLemmas to unassign them from an Editor.

## Assign Editors with PATCH Or Put To IssueLemmas

- Super users can PATCH and POST IssueLemmas to assign them to an Editor.
- Editors can not PATCH and POST IssueLemmas to assign them to an Editor.
- Authors can not PATCH and POST IssueLemmas to assign them to an Editor.

## GET (list) IssueLemmas With No Query

- Super users get objects with editor assignments.
- Editors get object without editor assignment.
- Authors get object without editor assignment.

## GET (list) IssueLemmas With Editor Assignment Query (?editor=id)

- Super users get filtered objects with editor assignments.
- Editors get object without editor assignment.
- Editors get a 403, if the query is for somone else.
- Authors get a 403.

## GET (retrieve) Single IssueLemmas With Assignments

- Super users the object with editor assignment.
- Editors get object without editor assignment.
- Authors get object without editor assignment.
"""
from typing import List
from django.db.models import Q
from rest_framework import status
from rest_framework.test import APITestCase

from oebl_irs_workflow.models import Author, Editor, IrsUser, IssueLemma
from oebl_irs_workflow.tests.utilities import LogOutMixin, EditorTestCaseMixin, AssignedIssueLemmaMixin, MixedIssueLemmasMixin, NotAssignedIssueLemmaMixin, create_and_login_user, create_valid_issue_lemma_json_for_editor


class PostTestCase(LogOutMixin, EditorTestCaseMixin, APITestCase):
    """
## POST IssueLemmas With Assignments

- Super users can POST IssueLemmas assigned to an Editor.
- Editors can not POST IssueLemmas assigned to an Editor.
- Authors can not POST IssueLemmas assigned to an Editor.

"""

    issue_lemma_json: dict

    def setUp(self) -> None:
        super().setUp()
        self.issue_lemma_json = create_valid_issue_lemma_json_for_editor(
            self.editor.pk)

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.post(
            '/workflow/api/v1/issue-lemma/', data=self.issue_lemma_json, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_201_CREATED, response.content)
        issue_lemma_id = response.json()['id']
        issue_lemma: IssueLemma = IssueLemma.objects.get(pk=issue_lemma_id)
        self.assertEqual(issue_lemma.editor, self.editor)

    def test_editor(self):
        create_and_login_user(Editor, self.client)
        response = self.client.post(
            '/workflow/api/v1/issue-lemma/', data=self.issue_lemma_json, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assertEqual(
            0,
            IssueLemma.objects.count()
        )

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.post(
            '/workflow/api/v1/issue-lemma/', data=self.issue_lemma_json, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assertEqual(
            0,
            IssueLemma.objects.count()
        )


class DeleteTestCase(LogOutMixin, AssignedIssueLemmaMixin, APITestCase):
    """
## DELETE IssueLemmas With Assignments

- Super users can DELETE IssueLemmas assigned to an Editor.
- Editors can not DELETE IssueLemmas assigned to an Editor.
- Authors can not DELETE IssueLemmas assigned to an Editor.
"""

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.delete(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            format='json',
        )
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT, response.content)
        self.assertEqual(
            0,
            IssueLemma.objects.count()
        )

    def test_editor(self):
        create_and_login_user(Editor, self.client)
        response = self.client.delete(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            format='json',
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assertEqual(
            1,
            IssueLemma.objects.count()
        )

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.delete(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            format='json',
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assertEqual(
            1,
            IssueLemma.objects.count()
        )


class UnassignTestCase(LogOutMixin, AssignedIssueLemmaMixin, APITestCase):
    """
## Unassign Editors with PATCH Or Put From IssueLemmas

- Super users can PATCH and POST IssueLemmas to unassign them from an Editor.
- Editors can not PATCH and POST IssueLemmas to unassign them from an Editor.
- Authors can not PATCH and POST IssueLemmas to unassign them from an Editor.
"""

    def test_superuser_patch(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data={
                'editor': None,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.assigned_issue_lemma.editor)

    def test_superuser_put(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data=create_valid_issue_lemma_json_for_editor(editor_id=None),
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.assigned_issue_lemma.editor)

    def test_editor_patch(self):
        create_and_login_user(Editor, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data={
                'editor': None,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNotNone(self.assigned_issue_lemma.editor)

    def test_editor_put(self):
        create_and_login_user(Editor, self.client)
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data=create_valid_issue_lemma_json_for_editor(editor_id=None),
            format='json'
        )

        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNotNone(self.assigned_issue_lemma.editor)

    def test_author_patch(self):
        create_and_login_user(Author, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data={
                'editor': None,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNotNone(self.assigned_issue_lemma.editor)

    def test_author_put(self):
        create_and_login_user(Author, self.client)
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/',
            data={
                **create_valid_issue_lemma_json_for_editor(editor_id=None),
                'id': self.assigned_issue_lemma.pk,
            },
            format='json'
        )

        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.assigned_issue_lemma.refresh_from_db()
        self.assertIsNotNone(self.assigned_issue_lemma.editor)


class AssignTestCase(LogOutMixin, NotAssignedIssueLemmaMixin, APITestCase):
    """
## Assign Editors with PATCH Or Put To IssueLemmas

- Super users can PATCH and POST IssueLemmas to assign them to an Editor.
- Editors can not PATCH and POST IssueLemmas to assign them to an Editor.
- Authors can not PATCH and POST IssueLemmas to assign them to an Editor.
"""

    def test_superuser_patch(self):
        create_and_login_user(IrsUser, self.client)
        editor = Editor.objects.create()
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data={
                'editor': editor.pk,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertEqual(self.not_assigned_issue_lemma.editor, editor)

    def test_superuser_put(self):
        create_and_login_user(IrsUser, self.client)
        editor = Editor.objects.create()
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data=create_valid_issue_lemma_json_for_editor(editor_id=editor.pk),
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertEqual(self.not_assigned_issue_lemma.editor, editor)

    def test_editor_patch(self):
        create_and_login_user(Editor, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data={
                'editor': Editor.objects.create().pk,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.not_assigned_issue_lemma.editor)

    def test_editor_put(self):
        create_and_login_user(Editor, self.client)
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data = create_valid_issue_lemma_json_for_editor(
                editor_id=Editor.objects.create().pk
            ),
            format='json'
        )

        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.not_assigned_issue_lemma.editor)

    def test_author_patch(self):
        create_and_login_user(Author, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data={
                'editor': Editor.objects.create().pk,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.not_assigned_issue_lemma.editor)

    def test_author_put(self):
        create_and_login_user(Author, self.client)
        response = self.client.put(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/',
            data=create_valid_issue_lemma_json_for_editor(
                    editor_id=Editor.objects.create().pk
            ),
            format='json'
        )

        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN, response.content)
        self.not_assigned_issue_lemma.refresh_from_db()
        self.assertIsNone(self.not_assigned_issue_lemma.editor)


class ListWithNoQueryTestAssignment(LogOutMixin, MixedIssueLemmasMixin, APITestCase):
    """
## GET (list) IssueLemmas With No Query

- Super users get objects with editor assignments.
- Editors get object without editor assignment.
- Authors get object without editor assignment.
"""

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get('/workflow/api/v1/issue-lemma/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['results']
        self.assertEqual(2, results.__len__())
        self.assertTrue(
            all(
                (
                    'editor' in result
                    for result in results
                )
            )
        )

    def test_editor(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get('/workflow/api/v1/issue-lemma/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results: List[dict] = data['results']
        self.assertEqual(2, results.__len__())

        # None of them should show assigned editors
        self.assertTrue(all('editor' not in result for result in results))

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.get('/workflow/api/v1/issue-lemma/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results: List[dict] = data['results']
        
        self.assertEqual(2, results.__len__())
        
        # None of them should show assigned editors
        self.assertTrue(all('editor' not in result for result in results))



class ListWithQueryTestAssignment(LogOutMixin, MixedIssueLemmasMixin, APITestCase):
    """
## GET (list) IssueLemmas With Editor Assignment Query (?editor=id)

- Super users get filtered objects with editor assignments.
- Editors get object without editor assignment.
- Editors get a 403, if the query is for somone else.
- Authors get a 403.
"""

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/?editor={self.editor.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results: List[dict] = data['results']
        self.assertEqual(1, results.__len__())
        self.assertEqual(results[0]['id'], self.assigned_issue_lemma.pk)

    def test_editor(self):
        self.client.login(username=self.editor.username, password='password')

        # - Editor get filtered objects if the query is for themselves – with editor assignments
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/?editor={self.editor.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results: List[dict] = data['results']
        self.assertEqual(1, results.__len__())
        result = results[0]
        self.assertEqual(result['id'], self.assigned_issue_lemma.pk)
        self.assertNotIn('editor', result)

        # - Editor get a 403, if the query is for somone else.
        other_editor_id = Editor.objects.filter(~Q(pk=self.editor)).first().pk
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/?editor={other_editor_id}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/?editor={self.editor.pk}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RetrieveTestCase(LogOutMixin, MixedIssueLemmasMixin, APITestCase):
    """
## GET (retrieve) Single IssueLemmas With Assignments

- Super users the object with editor assignment.
- Editors get object without editor assignment.
- Authors get object without editor assignment.
"""

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)

        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.assigned_issue_lemma.pk)

        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.not_assigned_issue_lemma.pk)

    def test_editor(self):
        self.client.login(username=self.editor.username, password='password')

        # - Editor get filtered object if the query is for themselves – with editor assignments
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.assigned_issue_lemma.pk)
        self.assertNotIn('editor', data)


        # - Editor gets data with no other editor info
        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.not_assigned_issue_lemma.pk)
        self.assertNotIn('editor', data)

    def test_author(self):
        create_and_login_user(Author, self.client)

        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.assigned_issue_lemma.pk)
        self.assertNotIn('editor', data)

        response = self.client.get(
            f'/workflow/api/v1/issue-lemma/{self.not_assigned_issue_lemma.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.not_assigned_issue_lemma.pk)
        self.assertNotIn('editor', data)
