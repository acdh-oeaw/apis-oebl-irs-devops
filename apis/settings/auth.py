from rest_framework.authentication import TokenAuthentication


class IRSTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"
