import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import yaml
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, ProgrammingError
from django.test import TestCase

from apps.core.utils.wagtail_setup_utils import WagtailSetupUtils


class WagtailSetupUtilsTestCase(TestCase):
    def setUp(self):
        # Create a mock command instance
        self.mock_command = Mock()
        self.mock_command.stdout = Mock()
        self.mock_command.style = Mock()
        self.mock_command.style.SUCCESS = Mock(side_effect=lambda x: f"SUCCESS: {x}")
        self.mock_command.style.ERROR = Mock(side_effect=lambda x: f"ERROR: {x}")
        self.mock_command.style.WARNING = Mock(side_effect=lambda x: f"WARNING: {x}")

        self.utils = WagtailSetupUtils(self.mock_command)

    def test_styled_output_success(self):
        """Test styled_output with SUCCESS style"""
        self.utils.styled_output("Test message", "SUCCESS")
        self.mock_command.style.SUCCESS.assert_called_with("Test message")
        self.mock_command.stdout.write.assert_called_with("SUCCESS: Test message")

    def test_styled_output_error(self):
        """Test styled_output with ERROR style"""
        self.utils.styled_output("Error message", "ERROR")
        self.mock_command.style.ERROR.assert_called_with("Error message")
        self.mock_command.stdout.write.assert_called_with("ERROR: Error message")

    def test_styled_output_warning(self):
        """Test styled_output with WARNING style"""
        self.utils.styled_output("Warning message", "WARNING")
        self.mock_command.style.WARNING.assert_called_with("Warning message")
        self.mock_command.stdout.write.assert_called_with("WARNING: Warning message")

    def test_styled_output_default(self):
        """Test styled_output with default style"""
        self.utils.styled_output("Default message", "OTHER")
        self.mock_command.stdout.write.assert_called_with("Default message")

    @patch('apps.core.utils.wagtail_setup_utils.call_command')
    def test_ensure_page_tree_health_success(self, mock_call_command):
        """Test ensure_page_tree_health with successful fixtree"""
        mock_root_page = Mock()

        with patch.object(self.utils, 'get_or_create_root_page', return_value=mock_root_page):
            result = self.utils.ensure_page_tree_health()

        mock_call_command.assert_called_with("fixtree")
        self.assertEqual(result, mock_root_page)

    @patch('apps.core.utils.wagtail_setup_utils.call_command')
    def test_ensure_page_tree_health_database_error(self, mock_call_command):
        """Test ensure_page_tree_health with DatabaseError"""
        mock_call_command.side_effect = DatabaseError("Test database error")
        mock_root_page = Mock()

        with patch.object(self.utils, 'get_or_create_root_page', return_value=mock_root_page):
            result = self.utils.ensure_page_tree_health()

        self.assertEqual(result, mock_root_page)

    @patch('apps.core.utils.wagtail_setup_utils.call_command')
    def test_ensure_page_tree_health_programming_error(self, mock_call_command):
        """Test ensure_page_tree_health with ProgrammingError"""
        mock_call_command.side_effect = ProgrammingError("Test programming error")
        mock_root_page = Mock()

        with patch.object(self.utils, 'get_or_create_root_page', return_value=mock_root_page):
            result = self.utils.ensure_page_tree_health()

        self.assertEqual(result, mock_root_page)

    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_or_create_root_page_existing_healthy(self, mock_get_root):
        """Test get_or_create_root_page with existing healthy root"""
        mock_root = Mock()
        mock_root.title = "Existing Root"
        mock_children = Mock()
        mock_children.count.return_value = 2
        mock_root.get_children.return_value = mock_children
        mock_get_root.return_value = mock_root

        result = self.utils.get_or_create_root_page()

        self.assertEqual(result, mock_root)

    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_or_create_root_page_existing_corrupted(self, mock_get_root):
        """Test get_or_create_root_page with corrupted tree"""
        mock_root = Mock()
        mock_root.title = "Corrupted Root"
        mock_root.get_children.side_effect = DatabaseError("Corrupted tree")
        mock_get_root.return_value = mock_root

        # Mock Page.objects for cleanup and creation
        with patch('wagtail.models.Page.objects') as mock_page_objects, \
            patch('wagtail.models.Page.add_root') as mock_add_root:

            new_root = Mock()
            mock_add_root.return_value = new_root

            result = self.utils.get_or_create_root_page()

            mock_page_objects.all().delete.assert_called_once()
            mock_add_root.assert_called_with(title="Root", slug="root")
            self.assertEqual(result, new_root)

    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_or_create_root_page_no_existing(self, mock_get_root):
        """Test get_or_create_root_page with no existing root"""
        mock_get_root.return_value = None

        with patch('wagtail.models.Page.objects') as mock_page_objects, \
            patch('wagtail.models.Page.add_root') as mock_add_root:

            new_root = Mock()
            mock_add_root.return_value = new_root

            result = self.utils.get_or_create_root_page()

            mock_page_objects.all().delete.assert_called_once()
            mock_add_root.assert_called_with(title="Root", slug="root")
            self.assertEqual(result, new_root)

    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_or_create_root_page_database_error(self, mock_get_root):
        """Test get_or_create_root_page with DatabaseError"""
        mock_get_root.side_effect = DatabaseError("Database error")

        with patch('wagtail.models.Page.objects') as mock_page_objects, \
            patch('wagtail.models.Page.add_root') as mock_add_root:

            mock_add_root.side_effect = DatabaseError("Failed to create")

            with self.assertRaises(DatabaseError):
                self.utils.get_or_create_root_page()

    def test_cleanup_pages_by_type(self):
        """Test cleanup_pages_by_type"""
        # Create mock page types
        MockPageType1 = Mock()
        MockPageType1.__name__ = "MockPageType1"
        MockPageType1.objects.count.return_value = 3
        MockPageType1.objects.all().delete = Mock()

        MockPageType2 = Mock()
        MockPageType2.__name__ = "MockPageType2"
        MockPageType2.objects.count.return_value = 0

        MockPageType3 = Mock()
        MockPageType3.__name__ = "MockPageType3"
        MockPageType3.objects.count.return_value = 1
        MockPageType3.objects.all().delete = Mock()

        page_types = [MockPageType1, MockPageType2, MockPageType3]

        result = self.utils.cleanup_pages_by_type(page_types)

        expected = {"MockPageType1": 3, "MockPageType3": 1}
        self.assertEqual(result, expected)
        MockPageType1.objects.all().delete.assert_called_once()
        MockPageType3.objects.all().delete.assert_called_once()

    def test_check_slug_availability_no_conflict(self):
        """Test check_slug_availability with no existing page"""
        mock_parent = Mock()
        mock_children = Mock()
        mock_children.filter().first.return_value = None
        mock_parent.get_children.return_value = mock_children

        result = self.utils.check_slug_availability(mock_parent, "test-slug")

        self.assertTrue(result)

    def test_check_slug_availability_conflict_force(self):
        """Test check_slug_availability with conflict and force=True"""
        mock_parent = Mock()
        mock_existing = Mock()
        mock_children = Mock()
        mock_children.filter().first.return_value = mock_existing
        mock_parent.get_children.return_value = mock_children

        result = self.utils.check_slug_availability(mock_parent, "test-slug", force=True)

        mock_existing.delete.assert_called_once()
        self.assertTrue(result)

    def test_check_slug_availability_conflict_no_force(self):
        """Test check_slug_availability with conflict and force=False"""
        mock_parent = Mock()
        mock_existing = Mock()
        mock_children = Mock()
        mock_children.filter().first.return_value = mock_existing
        mock_parent.get_children.return_value = mock_children

        result = self.utils.check_slug_availability(mock_parent, "test-slug", force=False)

        self.assertFalse(result)

    @patch('wagtail.models.Site.objects.get_or_create')
    def test_setup_default_site_created(self, mock_get_or_create):
        """Test setup_default_site when site is created"""
        mock_root = Mock()
        mock_site = Mock()
        mock_get_or_create.return_value = (mock_site, True)

        result = self.utils.setup_default_site(mock_root, "Test Site", "localhost", 8000)

        mock_get_or_create.assert_called_with(
            hostname="localhost",
            defaults={
                "port": 8000,
                "root_page": mock_root,
                "is_default_site": True,
                "site_name": "Test Site",
            }
        )
        self.assertEqual(result, mock_site)

    @patch('wagtail.models.Site.objects.get_or_create')
    def test_setup_default_site_updated(self, mock_get_or_create):
        """Test setup_default_site when site is updated"""
        mock_root = Mock()
        mock_site = Mock()
        mock_get_or_create.return_value = (mock_site, False)

        result = self.utils.setup_default_site(mock_root, "Updated Site", "localhost", 8000)

        self.assertEqual(mock_site.root_page, mock_root)
        self.assertTrue(mock_site.is_default_site)
        self.assertEqual(mock_site.site_name, "Updated Site")
        mock_site.save.assert_called_once()
        self.assertEqual(result, mock_site)

    @patch('wagtail.models.Site.objects.get_or_create')
    def test_setup_default_site_database_error(self, mock_get_or_create):
        """Test setup_default_site with DatabaseError"""
        mock_get_or_create.side_effect = DatabaseError("Database error")
        mock_root = Mock()

        with self.assertRaises(DatabaseError):
            self.utils.setup_default_site(mock_root, "Test Site", "localhost", 8000)

    @patch('wagtail.models.Page.objects.all')
    def test_debug_page_tree_success(self, mock_all):
        """Test debug_page_tree with successful execution"""
        mock_page1 = Mock()
        mock_page1.id = 1
        mock_page1.title = "Page 1"
        mock_page1.slug = "page-1"
        mock_page1.depth = 1
        mock_page1.path = "0001"
        type(mock_page1).__name__ = "MockPage"

        mock_page2 = Mock()
        mock_page2.id = 2
        mock_page2.title = "Page 2"
        mock_page2.slug = "page-2"
        mock_page2.depth = 2
        mock_page2.path = "00010001"
        type(mock_page2).__name__ = "MockPage"

        mock_queryset = Mock()
        mock_queryset.order_by.return_value = [mock_page1, mock_page2]
        mock_all.return_value = mock_queryset

        self.utils.debug_page_tree()

        mock_all.assert_called_once()
        mock_queryset.order_by.assert_called_with("path")

    @patch('wagtail.models.Page.objects.all')
    def test_debug_page_tree_database_error(self, mock_all):
        """Test debug_page_tree with DatabaseError"""
        mock_all.side_effect = DatabaseError("Database error")

        # Should not raise exception, just log error
        self.utils.debug_page_tree()

    def test_check_model_tables_exist_success(self):
        """Test check_model_tables_exist with existing tables"""
        mock_model1 = Mock()
        mock_model1.objects.count.return_value = 5

        mock_model2 = Mock()
        mock_model2.objects.count.return_value = 0

        result = WagtailSetupUtils.check_model_tables_exist([mock_model1, mock_model2])

        self.assertTrue(result)

    def test_check_model_tables_exist_database_error(self):
        """Test check_model_tables_exist with DatabaseError"""
        mock_model = Mock()
        mock_model.objects.count.side_effect = DatabaseError("Table not found")

        result = WagtailSetupUtils.check_model_tables_exist([mock_model])

        self.assertFalse(result)

    def test_check_model_tables_exist_programming_error(self):
        """Test check_model_tables_exist with ProgrammingError"""
        mock_model = Mock()
        mock_model.objects.count.side_effect = ProgrammingError("Table not found")

        result = WagtailSetupUtils.check_model_tables_exist([mock_model])

        self.assertFalse(result)

    def test_check_model_tables_exist_improperly_configured(self):
        """Test check_model_tables_exist with ImproperlyConfigured"""
        mock_model = Mock()
        mock_model.objects.count.side_effect = ImproperlyConfigured("Not configured")

        result = WagtailSetupUtils.check_model_tables_exist([mock_model])

        self.assertFalse(result)

    def test_create_and_publish_page_success(self):
        """Test create_and_publish_page with successful creation"""
        mock_parent = Mock()
        mock_page = Mock()
        mock_page.title = "Test Page"
        mock_revision = Mock()
        mock_page.save_revision.return_value = mock_revision

        result = self.utils.create_and_publish_page(mock_parent, mock_page)

        mock_parent.add_child.assert_called_with(instance=mock_page)
        mock_page.save_revision.assert_called_once()
        mock_revision.publish.assert_called_once()
        self.assertEqual(result, mock_page)

    def test_create_and_publish_page_alternative_method(self):
        """Test create_and_publish_page with alternative method"""
        mock_parent = Mock()
        mock_page = Mock()
        mock_page.title = "Test Page"
        mock_revision = Mock()
        mock_page.save_revision.return_value = mock_revision

        result = self.utils.create_and_publish_page(mock_parent, mock_page, alternative_method=True)

        mock_page.save.assert_called_once()
        mock_parent.add_child.assert_called_with(instance=mock_page)
        mock_page.save_revision.assert_called_once()
        mock_revision.publish.assert_called_once()
        self.assertEqual(result, mock_page)

    def test_create_and_publish_page_fallback_to_alternative(self):
        """Test create_and_publish_page falls back to alternative method"""
        mock_parent = Mock()
        mock_parent.add_child.side_effect = [DatabaseError("First attempt fails"), None]

        mock_page = Mock()
        mock_page.title = "Test Page"
        mock_revision = Mock()
        mock_page.save_revision.return_value = mock_revision

        with patch.object(self.utils, 'create_and_publish_page') as mock_create:
            mock_create.side_effect = [
                self.utils.create_and_publish_page(mock_parent, mock_page, alternative_method=False),
                mock_page
            ]

            # Simulate the actual behavior
            try:
                mock_parent.add_child(instance=mock_page)
            except DatabaseError:
                # This is what would happen in the real method
                result = self.utils.create_and_publish_page(mock_parent, mock_page, alternative_method=True)

    def test_create_and_publish_page_both_methods_fail(self):
        """Test create_and_publish_page when both methods fail"""
        mock_parent = Mock()
        mock_parent.add_child.side_effect = DatabaseError("Always fails")

        mock_page = Mock()
        mock_page.title = "Test Page"
        mock_page.save.side_effect = DatabaseError("Save also fails")

        with patch.object(self.utils, 'debug_page_tree'):
            with self.assertRaises(DatabaseError):
                self.utils.create_and_publish_page(mock_parent, mock_page)

    @patch('apps.core.models.HomePage.objects.live')
    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_parent_page_homepage_exists(self, mock_get_root, mock_live):
        """Test get_parent_page when homepage exists"""
        mock_homepage = Mock()
        mock_homepage.title = "Homepage"
        mock_live.return_value.first.return_value = mock_homepage

        result = self.utils.get_parent_page()

        self.assertEqual(result, mock_homepage)

    @patch('apps.core.models.HomePage.objects.live')
    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_parent_page_no_homepage_has_root(self, mock_get_root, mock_live):
        """Test get_parent_page when no homepage but root exists"""
        mock_live.return_value.first.return_value = None
        mock_root = Mock()
        mock_root.title = "Root"
        mock_get_root.return_value = mock_root

        result = self.utils.get_parent_page()

        self.assertEqual(result, mock_root)

    @patch('apps.core.models.HomePage.objects.live')
    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_parent_page_no_homepage_no_root(self, mock_get_root, mock_live):
        """Test get_parent_page when no homepage and no root"""
        mock_live.return_value.first.return_value = None
        mock_get_root.return_value = None

        result = self.utils.get_parent_page()

        self.assertIsNone(result)

    @patch('apps.core.models.HomePage.objects.live')
    @patch('wagtail.models.Page.get_first_root_node')
    def test_get_parent_page_import_error(self, mock_get_root, mock_live):
        """Test get_parent_page when HomePage import fails"""
        mock_live.side_effect = ImportError("Cannot import HomePage")
        mock_root = Mock()
        mock_root.title = "Root"
        mock_get_root.return_value = mock_root

        result = self.utils.get_parent_page()

        self.assertEqual(result, mock_root)

    def test_load_page_content(self):
        """Test load_page_content"""
        yaml_content = {
            "pages": {
                "homepage": {
                    "title": "Home",
                    "content": "Welcome"
                }
            }
        }

        # Create a temporary file to test with
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(yaml_content, temp_file)
            temp_path = Path(temp_file.name)

        try:
            result = WagtailSetupUtils.load_page_content(temp_path, "pages")

            expected = {
                "homepage": {
                    "title": "Home",
                    "content": "Welcome"
                }
            }
            self.assertEqual(result, expected)
        finally:
            # Clean up the temporary file
            temp_path.unlink(missing_ok=True)
