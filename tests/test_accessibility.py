"""
Test accessibility auditing.
"""
import os

from mock import patch

from bok_choy.web_app_test import WebAppTest
from bok_choy.page_object import AccessibilityError

from .pages import AccessibilityPage


class NoAccessibilityTest(WebAppTest):
    """
    Test unsupported accessibility audit configuration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def test_axs_audit_firefox(self):
        page = AccessibilityPage(self.browser).visit()
        with self.assertRaises(NotImplementedError):
            page.do_axs_audit()


class AccessibilityTest(WebAppTest):
    """
    Test accessibility audit integration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(AccessibilityTest, self).setUp()
        self.ax_aria_04_errors = u'{}{}{}{}'.format(
            'Error: AX_ARIA_04 ',
            '(ARIA state and property values must be valid) failed on the following ',
            'element:\n',
            '#AX_ARIA_04_bad')
        self.ax_aria_01_errors = u'{}{}{}{}{}{}'.format(
            'Error: AX_ARIA_01 ',
            '(Elements with ARIA roles must use a valid, non-abstract ARIA role) failed on the following ',
            'elements (1 - 2 of 2):\n',
            '#AX_ARIA_01_not_a_role\n#AX_ARIA_01_empty_role\n',
            'See https://github.com/GoogleChrome/accessibility-developer-tools/wiki/Audit-Rules',
            '#-ax_aria_01--elements-with-aria-roles-must-use-a-valid-non-abstract-aria-role for more information.')

    def test_axs_audit_no_rules_by_default(self):
        # Default page object definition is to not check any rules
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()
        self.assertIsNone(report)

    @patch('tests.pages.AccessibilityPage.axs_audit_rules')
    def test_axs_audit_phantom(self, mock_rules):
        mock_rules.return_value = []
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # When checking all rules, results are 2 errors and 0 warnings
        self.assertEqual(2, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)
        self.assertEqual(result.errors[1], self.ax_aria_01_errors)

        self.assertEqual(0, len(result.warnings))

    @patch('tests.pages.AccessibilityPage.axs_scope')
    @patch('tests.pages.AccessibilityPage.axs_audit_rules')
    def test_axs_audit_limit_scope(self, mock_rules, mock_scope):
        # Limit the scope to the div with AX_ARIA_04 violations
        mock_scope.return_value = 'document.querySelector("#limit_scope")'
        mock_rules.return_value = []
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        # Make sure the mock was really called
        mock_scope.assert_called_once_with()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(0, len(result.warnings))

    @patch('tests.pages.AccessibilityPage.axs_audit_rules')
    def test_axs_audit_limit_rules(self, mock_rules):
        # Limit the rules checked to AX_ARIA_01
        mock_rules.return_value = ['badAriaRole']
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        # Make sure the mock was really called
        mock_rules.assert_called_once_with()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_01_errors)

        self.assertEqual(0, len(result.warnings))


class VerifyAccessibilityTest(WebAppTest):
    """
    Test accessibility audit integration that happens implicitly on
    a call that invokes wait_for_page.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(VerifyAccessibilityTest, self).setUp()

    @patch.dict(os.environ, {'VERIFY_ACCESSIBILITY': 'Yes'})
    @patch('tests.pages.AccessibilityPage.axs_audit_rules')
    def test_axs_audit_check_on_visit(self, mock_rules):
        mock_rules.return_value = []
        page = AccessibilityPage(self.browser)
        with self.assertRaises(AccessibilityError):
            page.visit()
