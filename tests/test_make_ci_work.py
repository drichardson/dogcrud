def test_delete_me_after_adding_another_test():
    """
    hatch test fails if there are no tests.

    When I setup CI, I wanted to add the test runner so it will just work when tests are added.

    So, I added this empty test that should be deleted as soon as another real test is added.
    """
