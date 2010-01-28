"""

Launching all doctests in the tests directory using:

    - The test_suite helper from the testing product
    - the base FunctionalTestCase in base.py

"""

from Products.csvreplicata.tests.base import FunctionalTestCase, setup_site
from Products.csvreplicata.tests.suite import test_doctests_suite as ts

################################################################################
# GLOBALS avalaible in doctests
# IMPORT/DEFINE objects there or inside ./user_globals.py (better)
# globals from the testing product are also available.
################################################################################
# example:
# from for import bar
# and in your doctests, you can do:
# >>> bar.something
from Products.csvreplicata.tests.globals import *
################################################################################

def test_suite():
    """."""
    setup_site()
    return ts(
        __file__,
        #patterns = ['(handl|basic).*txt$'],
        patterns = ['.*txt$'],
        globs=globals(),
        testklass=FunctionalTestCase
    )

# vim:set ft=python:
