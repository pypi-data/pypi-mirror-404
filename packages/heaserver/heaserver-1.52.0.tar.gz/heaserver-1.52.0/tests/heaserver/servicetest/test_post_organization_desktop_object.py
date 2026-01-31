from heaserver.service.testcase.mixin import PostMixin
from .organizationtestcase import PostOrganizationTestCase


class TestPostOrganization(PostOrganizationTestCase, PostMixin):  # type: ignore
    pass

