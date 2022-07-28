"""
# Summary Of Test Rules In this Module

Test rules regarding the assignment of authors to IssueLemmas via AuthorIssueLemmaAssignment.

Superusers can do everything, Authors can not assign, Editors and Authors can only view their assignments (via IssueLemma or AuthorIssueLemmaAssignment),
Authors can not change data, editors can only change data of assignments for articles, they are assigned to.

TODO: Clearer Description! For now, there are test failure messages, which have the same content / the rules.

"""

from django.db.models.query_utils import Q
from oebl_irs_workflow.models import Author, AuthorIssueLemmaAssignment, EditTypes, IrsUser
from rest_framework import status
from oebl_irs_workflow.tests.utilities import FullAssignmentMixin, MixedIssueLemmasMixin, LogOutMixin, create_and_login_user
from rest_framework.test import APITestCase


class PostTestCase(LogOutMixin, MixedIssueLemmasMixin, APITestCase):
    """
    Permissions for posting author assignments
    """

    author: Author

    def setUp(self):
        super().setUp()
        self.author = Author.objects.create()

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.post(
            '/workflow/api/v1/author-issue-assignment/',
            format='json',
            data={
                'issue_lemma': self.assigned_issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': EditTypes.WRITE,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Super users should have no restrictions')
        self.assertTrue(
            AuthorIssueLemmaAssignment.objects.filter(
                issue_lemma=self.assigned_issue_lemma,
                author=self.author,
                edit_type=EditTypes.WRITE
            ).exists(),
            'After posting an assignment, it should be in the database'
        )

    def test_editor_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.post(
            '/workflow/api/v1/author-issue-assignment/',
            format='json',
            data={
                'issue_lemma': self.assigned_issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': EditTypes.WRITE,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Editors should be able to post assignments for issues, they are assigned to.')
        self.assertTrue(
            AuthorIssueLemmaAssignment.objects.filter(
                issue_lemma=self.assigned_issue_lemma,
                author=self.author,
                edit_type=EditTypes.WRITE
            ).exists(),
            'After posting an assignment, it should be in the database'
        )

    def test_editor_not_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.post(
            '/workflow/api/v1/author-issue-assignment/',
            format='json',
            data={
                'issue_lemma': self.not_assigned_issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': EditTypes.WRITE,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors should not be able to post assignments for issues, they are not assigned to.')
        self.assertFalse(
            AuthorIssueLemmaAssignment.objects.filter(
                issue_lemma=self.assigned_issue_lemma,
                author=self.author,
                edit_type=EditTypes.WRITE
            ).exists(),
            'After failing to post an assignment, it should not be in the database'
        )

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.post(
            '/workflow/api/v1/author-issue-assignment/',
            format='json',
            data={
                'issue_lemma': self.assigned_issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': EditTypes.WRITE,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not post assignments')
        self.assertFalse(
            AuthorIssueLemmaAssignment.objects.filter(
                issue_lemma=self.assigned_issue_lemma,
                author=self.author,
                edit_type=EditTypes.WRITE
            ).exists(),
            'After failing to post an assignment, it should not be in the database'
        )


class DeleteTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'Super users can delete everything.')
        self.assertFalse(AuthorIssueLemmaAssignment.objects.exists(
        ), 'After deleting, the assignment should not be in the database.')

    def test_editor_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'Editors can delete assignments for issues, they are asssigned to.')
        self.assertFalse(AuthorIssueLemmaAssignment.objects.filter(
            pk=self.editor_controlled_author_assignment.pk).exists(),
            'After deleting, the assignment should not be in the database.'
        )

    def test_editor_not_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors can not delete assignments for issues, they are not asssigned to.')
        self.assertTrue(AuthorIssueLemmaAssignment.objects.filter(
            pk=self.editor_uncontrolled_author_assignment.pk).exists(),
            'After failing to delete, the assignment should still be in the database.'
        )

    def test_author(self):
        create_and_login_user(Author, self.client)
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not delete assignments.')
        response = self.client.delete(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not delete assignments.')
        self.assertEqual(
            2,
            AuthorIssueLemmaAssignment.objects.count(),
            'After failing to delete, the assignments should still be in the database.'
        )


class ReassignTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    some_other_author: Author

    def setUp(self):
        super().setUp()
        self.some_other_author = Author.objects.create()

    def test_superuser_patch(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'author': self.some_other_author.pk,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Super users can patch assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                         'After patching, the data should have changed')

    def test_superuser_put(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.some_other_author.pk,
                'edit_type': self.editor_controlled_author_assignment.edit_type,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Super users can PUT assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                         'After PUT, the data should have changed')

    def test_editor_assigned_patch(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'author': self.some_other_author.pk,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Editors can change assignments for issues, they are assigned to.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                         'After PATCH, the data should have changed')

    def test_editor_assigned_put(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.some_other_author.pk,
                'edit_type': self.editor_controlled_author_assignment.edit_type,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Editors can change assignments for issues, they are assigned to.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.some_other_author,
                         self.editor_controlled_author_assignment.author), 'After PUT, the data should have changed'

    def test_editor_not_assigned_patch(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/',
            format='json',
            data={
                'author': self.some_other_author.pk,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors can not change assignments for issues, they are not assigned to.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                            'After failing PATCH, the data should not be changed')

    def test_editor_not_assigned_put(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.some_other_author.pk,
                'edit_type': self.editor_controlled_author_assignment.edit_type,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors can not change assignments for issues, they are not assigned to.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                            'After failing PUT, the data should not be changed')

    def test_author_patch(self):
        create_and_login_user(Author, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/',
            format='json',
            data={
                'author': self.some_other_author.pk,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not change assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                            'After failing PATCH, the data should not be changed')

    def test_author_put(self):
        create_and_login_user(Author, self.client)
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.some_other_author.pk,
                'edit_type': self.editor_controlled_author_assignment.edit_type,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not change assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.some_other_author, self.editor_controlled_author_assignment.author,
                            'After failing PUT, the data should not be changed')


class ChangeAssignmentTypeTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    NEW_EDIT_TYPE: EditTypes = EditTypes.VIEW

    def test_superuser_patch(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Super users and change edit types.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                         'After submitting a change, the database should have new data.')

    def test_superuser_put(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Super users and change edit types.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                         'After submitting a change, the database should have new data.')

    def test_editor_assigned_patch(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Editors can change assignments for issue, they are responsible for.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                         'After submitting a change, the database should have new data.')

    def test_editor_assigned_put(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Editors can change assignments for issue, they are responsible for.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                         'After submitting a change, the database should have new data.')

    def test_editor_not_assigned_patch(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/',
            format='json',
            data={
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors can not change assignments for issue, they are not responsible for.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                            'After failing to submit a change, the database should not have new data.')

    def test_editor_not_assigned_put(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Editors can not change assignments for issue, they are not responsible for.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                            'After failing to submit a change, the database should not have new data.')

    def test_author_patch(self):
        create_and_login_user(Author, self.client)
        response = self.client.patch(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/',
            format='json',
            data={
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not change assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                            'After failing to submit a change, the database should not have new data.')

    def test_author_put(self):
        create_and_login_user(Author, self.client)
        response = self.client.put(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/',
            format='json',
            data={
                'issue_lemma': self.editor_controlled_author_assignment.issue_lemma.pk,
                'author': self.author.pk,
                'edit_type': self.NEW_EDIT_TYPE,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Authors can not change assignments.')
        self.editor_controlled_author_assignment.refresh_from_db()
        self.assertNotEqual(self.NEW_EDIT_TYPE, self.editor_controlled_author_assignment.edit_type,
                            'After failing to submit a change, the database should not have new data.')


class ListWithNoQueryTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    def setUp(self):
        super().setUp()
        # Set a third assignment, that our author should not see
        AuthorIssueLemmaAssignment.objects.create(
            issue_lemma=self.not_assigned_issue_lemma,  # Not assigned to the editor
            author=Author.objects.create(),  # Not assigned to the author
            edit_type=EditTypes.ANNOTATE,
        )

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get('/workflow/api/v1/author-issue-assignment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            3, len(results), 'Superuser should see all assignments')

    def test_editor(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get('/workflow/api/v1/author-issue-assignment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(1, len(
            results), 'Editor should only see assignments for issues, assigned to */her/him')
        assignment = results[0]
        self.assertEqual(
            assignment['id'], self.editor_controlled_author_assignment.pk)

    def test_author(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get('/workflow/api/v1/author-issue-assignment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(2, len(
            results), 'Author should only see assignments for issues, assigned to */her/him')
        self.assertTrue(
            all((assignment['author'] == self.author.pk for assignment in results)))


class ListWithQueryTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    def setUp(self):
        super().setUp()
        # Set a third assignment, that our author should not see
        AuthorIssueLemmaAssignment.objects.create(
            issue_lemma=self.not_assigned_issue_lemma,  # Not assigned to the editor
            author=Author.objects.create(),  # Not assigned to the author
            edit_type=EditTypes.ANNOTATE,
        )

    def test_superuser_issue_query(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?issue-lemma={self.assigned_issue_lemma.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            1, len(results), 'Superuser should see all assignments of issue lemma')
        self.assertEqual(self.assigned_issue_lemma.pk, results[0]['id'])

    def test_superuser_author_query(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?author={self.author.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            2, len(results), 'Superuser should see all assignments of author')
        self.assertTrue(
            all((result['author'] == self.author.pk for result in results)))

    def test_superuser_edit_type_query(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?edit_type={self.EDIT_TYPE}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            2, len(results), 'Superuser should see all assignments for edit type')
        self.assertTrue(
            all((result['edit_type'] == self.EDIT_TYPE for result in results)))

    def test_editor_assigned_issue_query(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?issue-lemma={self.assigned_issue_lemma.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(1, len(
            results), 'Editor should see all assignments for issue lemma assigned to editor')
        self.assertEqual(self.assigned_issue_lemma.pk, results[0]['id'])

    def test_editor_not_assigned_issue_query(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?issue-lemma={self.not_assigned_issue_lemma.pk}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_author_query(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?author={self.author.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(1, len(
            results), 'Editor should see all assignments of author for */her/his assigned issues')
        self.assertTrue(
            all((result['author'] == self.author.pk for result in results)))

    def test_editor_edit_type_query(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?edit_type={self.EDIT_TYPE}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            1, len(results), 'Superuser should see all assignments for edit type')
        self.assertTrue(
            all((result['edit_type'] == self.EDIT_TYPE for result in results)))

    def test_author_issue_query(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?issue-lemma={self.not_assigned_issue_lemma.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(1, len(
            results), 'Author should see all assignments for issue lemma assigned to author (There are 2, one for another author)')
        self.assertEqual(self.not_assigned_issue_lemma.pk, results[0]['id'])

    def test_author_self_query(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?author={self.author.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            2, len(results), 'Author should see all own assignments')
        self.assertTrue(
            all((result['author'] == self.author.pk for result in results)))

    def test_author_other_author_query(self):
        self.client.login(username=self.author.username, password='password')
        other_author = Author.objects.filter(~Q(pk=self.author.pk)).first()
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?issue-lemma={other_author.pk}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_edit_type_query(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/?edit_type={self.EDIT_TYPE}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(
            2, len(results), 'Author should see all own assignments for edit type')
        self.assertTrue(
            all((result['edit_type'] == self.EDIT_TYPE for result in results)))


class RetrieveTestCase(LogOutMixin, FullAssignmentMixin, APITestCase):

    assignment_to_other_author: AuthorIssueLemmaAssignment

    def setUp(self):
        super().setUp()
        # Set a third assignment, that our author should not see
        self.assignment_to_other_author = AuthorIssueLemmaAssignment.objects.create(
            issue_lemma=self.not_assigned_issue_lemma,  # Not assigned to the editor
            author=Author.objects.create(),  # Not assigned to the author
            edit_type=EditTypes.ANNOTATE,
        )

    def test_superuser(self):
        create_and_login_user(IrsUser, self.client)
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.assigned_issue_lemma.pk, response.json()['id'])

    def test_editor_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.assigned_issue_lemma.pk, response.json()['id'])

    def test_editor_not_assigned(self):
        self.client.login(username=self.editor.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_uncontrolled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_assigned(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/{self.editor_controlled_author_assignment.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.assigned_issue_lemma.pk, response.json()['id'])

    def test_author_not_assigned(self):
        self.client.login(username=self.author.username, password='password')
        response = self.client.get(
            f'/workflow/api/v1/author-issue-assignment/{self.assignment_to_other_author.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
