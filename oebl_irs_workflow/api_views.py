from typing import Type, Union
from oebl_irs_workflow.permission import AuthorIssueLemmaAssignmentPermissions, IssueLemmaEditorAssignmentPermissions, extract_permission_relevant_user_type
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer, extend_schema, extend_schema_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import QuerySet, Subquery


from .models import (
    Author,
    Issue,
    IssueLemma,
    LemmaStatus,
    LemmaNote,
    Lemma,
    LemmaLabel,
    Editor,
    AuthorIssueLemmaAssignment,
)
from .serializer_rl2wf import ResearchLemma2WorkflowLemmaSerializer
from .serializers import (
    AuthorIssueLemmaAssignmentSerializer,
    IssueLemmaNoEditorSerializer,
    UserDetailSerializer,
    AuthorSerializer,
    EditorSerializer,
    IssueSerializer,
    IssueLemmaSerializer,
    LemmaStatusSerializer,
    LemmaNoteSerializer,
    LemmaSerializer,
    LemmaLabelSerializer,
)


class UserProfileViewset(viewsets.ViewSet):
    """Viewset to show UserProfile of current User"""

    def list(self, request):
        user = UserDetailSerializer(request.user)
        return Response(user.data)


class AuthorViewset(viewsets.ReadOnlyModelViewSet):
    """Viewset to retrieve Author objects"""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_fields = ["username"]
    permission_classes = [IsAuthenticated]


class EditorViewset(viewsets.ReadOnlyModelViewSet):
    """Viewset to retrieve Editor objects"""

    queryset = Editor.objects.all()
    serializer_class = EditorSerializer
    filterset_fields = ["username"]
    permission_classes = [IsAuthenticated]


class IssueViewset(viewsets.ModelViewSet):

    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    filter_fields = ["name", "pubDate"]
    permission_classes = [IsAuthenticated]

@extend_schema_view(
    list = extend_schema(responses=IssueLemmaSerializer),
    retrieve = extend_schema(responses=IssueLemmaSerializer),
    create = extend_schema(responses=IssueLemmaSerializer),
    update = extend_schema(responses=IssueLemmaSerializer),
    partial_update = extend_schema(responses=IssueLemmaSerializer),
    destroy  = extend_schema(responses=IssueLemmaSerializer),
)
class IssueLemmaViewset(viewsets.ModelViewSet):

    queryset = IssueLemma.objects.all()
    filter_fields = ["lemma", "issue", "editor", ]
    http_method_names = ["get", "post", "head", "options", "delete", "update", "patch", "put", ]
    permission_classes = [IsAuthenticated, IssueLemmaEditorAssignmentPermissions]

    def get_serializer_class(self) -> Union[Type[IssueLemmaNoEditorSerializer], Type[IssueLemmaSerializer]]:
        """
        Super users can see, which editor is assigned to an IssueLemma, authors and editors can not.
        """
        if self.request.user.is_superuser:
            return IssueLemmaSerializer
        else:
            return IssueLemmaNoEditorSerializer


class LemmaViewset(viewsets.ReadOnlyModelViewSet):

    queryset = Lemma.objects.all()
    serializer_class = LemmaSerializer
    permission_classes = [IsAuthenticated]


class LemmaNoteViewset(viewsets.ModelViewSet):

    queryset = LemmaNote.objects.all()
    serializer_class = LemmaNoteSerializer
    filter_fields = ["lemma"]
    permission_classes = [IsAuthenticated]


class LemmaStatusViewset(viewsets.ModelViewSet):

    queryset = LemmaStatus.objects.all()
    serializer_class = LemmaStatusSerializer
    filter_fields = ["issuelemma", "issue"]
    permission_classes = [IsAuthenticated]


class LemmaLabelViewset(viewsets.ModelViewSet):

    queryset = LemmaLabel.objects.all()
    serializer_class = LemmaLabelSerializer
    filter_fields = ["issuelemma"]
    permission_classes = [IsAuthenticated]


@extend_schema(
    description="""Endpoint that allows to POST a list of lemmas to the research pipeline for processing.
        All additional fields not mentioned in the Schema are stored and retrieved as user specific fields.
        """,
    methods=["POST"],
    request=ResearchLemma2WorkflowLemmaSerializer,
    responses={
        201: inline_serializer(
            many=False,
            name="ResearchLemma2WorkfloweResponse",
            fields={"success": serializers.UUIDField()},
        ),
    },
)
class ResearchLemma2WorkflowLemma(APIView):
    def post(self, request, format=None):
        serializer = ResearchLemma2WorkflowLemmaSerializer(data=request.data)
        if serializer.is_valid():
            res = serializer.create(serializer.data, request.user)
            return Response(res, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthorIssueLemmaAssignmentViewSet(viewsets.ModelViewSet):
    
    serializer_class = AuthorIssueLemmaAssignmentSerializer
    permission_classes = [IsAuthenticated, AuthorIssueLemmaAssignmentPermissions, ]
    filter_fields = ['issue_lemma', 'author', 'edit_type', ]


    def get_queryset(self) -> 'QuerySet':
        
        user: 'User' = self.request.user
        query_all: 'QuerySet' = AuthorIssueLemmaAssignment.objects.all()

        if user.is_superuser:
            return query_all
        
        permission_relevant_user = extract_permission_relevant_user_type(user)

        if permission_relevant_user.__class__ is Author:
            return query_all.filter(author=permission_relevant_user)
        elif permission_relevant_user.__class__ is Editor:
            return query_all.filter(issue_lemma__in=Subquery(IssueLemma.objects.filter(editor=permission_relevant_user).values('pk')))       
        else:
            raise TypeError('Bad programming. Type guards did not work!')

        