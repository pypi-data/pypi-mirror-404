"""
Tests for sbom-git-sm main module.

Copyright (c) 2025-2026 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sbom_git_sm.main import (
    create_sbom, 
    analyze_repo_recursive, 
    convert_to_cyclonedx, 
    process_repo_as_component,
    process_repo_as_nested_component,
    is_git_repo,
    get_repo_info,
    get_submodules,
    strip_username_from_url,
    add_version_source_property
)

from sbom_git_sm.version_config import VersionConfig


class TestGitRepoFunctions(unittest.TestCase):
    """Tests for the Git repository analysis functions."""

    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_is_git_repo_true(self, mock_run):
        """Test is_git_repo when the path is a valid Git repository."""
        # Mock the subprocess.run result
        mock_process = mock.Mock()
        mock_process.returncode = 0
        mock_process.stdout = "true"
        mock_run.return_value = mock_process

        # Call the function
        result = is_git_repo("/path/to/repo")

        # Check the result
        self.assertTrue(result)
        mock_run.assert_called_once()

    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_is_git_repo_false(self, mock_run):
        """Test is_git_repo when the path is not a valid Git repository."""
        # Mock the subprocess.run result
        mock_process = mock.Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        # Call the function
        result = is_git_repo("/path/to/not/repo")

        # Check the result
        self.assertFalse(result)
        mock_run.assert_called_once()

    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_get_repo_info(self, mock_run):
        """Test get_repo_info with mocked subprocess calls."""
        # Mock the subprocess.run results for each call
        mock_results = [
            # hash_result
            mock.Mock(returncode=0, stdout="abcdef1234567890"),
            # branch_result
            mock.Mock(returncode=0, stdout="main"),
            # tags_result
            mock.Mock(returncode=0, stdout="v1.0.0\nv1.0.1"),
            # url_result
            mock.Mock(returncode=0, stdout="https://github.com/user/repo.git")
        ]
        mock_run.side_effect = mock_results

        # Call the function
        repo_info = get_repo_info("/path/to/repo", "/path/to/repo")

        # Check the result
        self.assertEqual(repo_info["hash"], "abcdef1234567890")
        self.assertEqual(repo_info["branch"], "main")
        self.assertEqual(repo_info["tags"], ["v1.0.0", "v1.0.1"])
        self.assertTrue(repo_info["has_tag"])
        self.assertEqual(repo_info["url"], "https://github.com/user/repo.git")
        self.assertEqual(len(repo_info["submodules"]), 0)
        self.assertEqual(mock_run.call_count, 4)

    @mock.patch('sbom_git_sm.main.os.path.isfile')
    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_get_submodules(self, mock_run, mock_isfile):
        """Test get_submodules with mocked subprocess calls."""
        # Mock os.path.isfile to return True for .gitmodules
        mock_isfile.return_value = True

        # Mock the subprocess.run results
        mock_path_result = mock.Mock(
            returncode=0, 
            stdout="submodule.module1.path module1\nsubmodule.module2.path module2"
        )
        mock_url_result1 = mock.Mock(
            returncode=0, 
            stdout="https://github.com/user/module1.git"
        )
        mock_url_result2 = mock.Mock(
            returncode=0, 
            stdout="https://github.com/user/module2.git"
        )
        mock_run.side_effect = [mock_path_result, mock_url_result1, mock_url_result2]

        # Call the function
        submodules = get_submodules("/path/to/repo")

        # Check the result
        self.assertEqual(len(submodules), 2)
        self.assertEqual(submodules[0]["name"], "module1")
        self.assertEqual(submodules[0]["path"], "module1")
        self.assertEqual(submodules[0]["url"], "https://github.com/user/module1.git")
        self.assertEqual(submodules[1]["name"], "module2")
        self.assertEqual(submodules[1]["path"], "module2")
        self.assertEqual(submodules[1]["url"], "https://github.com/user/module2.git")
        self.assertEqual(mock_run.call_count, 3)
        
    def test_strip_username_from_url(self):
        """Test strip_username_from_url with various URL formats."""
        # Test with URL containing username
        url1 = "https://username@github.com/user/repo.git"
        self.assertEqual(strip_username_from_url(url1), "https://github.com/user/repo.git")
        
        # Test with URL containing username and organization
        url2 = "https://JaMDE@dev.azure.com/JaMDE/PyUTL/_git/UTL_sbom_git_sm"
        self.assertEqual(strip_username_from_url(url2), "https://dev.azure.com/JaMDE/PyUTL/_git/UTL_sbom_git_sm")
        
        # Test with URL without username
        url3 = "https://github.com/user/repo.git"
        self.assertEqual(strip_username_from_url(url3), "https://github.com/user/repo.git")
        
        # Test with empty URL
        url4 = ""
        self.assertEqual(strip_username_from_url(url4), "")
        
        # Test with None URL
        url5 = None
        self.assertEqual(strip_username_from_url(url5), None)
        
        # Test with HTTP URL
        url6 = "http://username@github.com/user/repo.git"
        self.assertEqual(strip_username_from_url(url6), "http://github.com/user/repo.git")
        
        # Test with URL containing username with special characters
        url7 = "https://user.name@github.com/user/repo.git"
        self.assertEqual(strip_username_from_url(url7), "https://github.com/user/repo.git")


class TestCycloneDXFunctions(unittest.TestCase):
    """Tests for the CycloneDX conversion functions."""

    def test_convert_to_cyclonedx(self):
        """Test convert_to_cyclonedx with a sample repository info."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Convert to CycloneDX (default: application for main repo, use_nested_components=False)
        cyclonedx = convert_to_cyclonedx(repo_info, use_nested_components=False)

        # Check the result
        self.assertEqual(cyclonedx["bomFormat"], "CycloneDX")
        self.assertEqual(cyclonedx["specVersion"], "1.4")
        self.assertTrue(cyclonedx["serialNumber"].startswith("urn:uuid:"))
        self.assertEqual(cyclonedx["version"], 1)
        self.assertIn("metadata", cyclonedx)
        self.assertIn("timestamp", cyclonedx["metadata"])
        self.assertIn("tools", cyclonedx["metadata"])
        self.assertEqual(len(cyclonedx["metadata"]["tools"]), 1)
        self.assertEqual(cyclonedx["metadata"]["tools"][0]["name"], "sbom-git-sm")
        self.assertIn("components", cyclonedx)
        self.assertEqual(len(cyclonedx["components"]), 1)
        # Main repo should be application type by default
        self.assertEqual(cyclonedx["components"][0]["type"], "application")
        # Should have a dependencies section when use_nested_components=False
        self.assertIn("dependencies", cyclonedx)
        # Component should have a bom-ref
        self.assertIn("bom-ref", cyclonedx["components"][0])
        
    def test_convert_to_cyclonedx_with_component_type(self):
        """Test convert_to_cyclonedx with a custom component type."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Convert to CycloneDX with custom component type and use_nested_components=False
        cyclonedx = convert_to_cyclonedx(repo_info, component_type="operating-system", use_nested_components=False)

        # Check the result
        self.assertEqual(cyclonedx["components"][0]["type"], "operating-system")
        # Should have a dependencies section when use_nested_components=False
        self.assertIn("dependencies", cyclonedx)
        # Component should have a bom-ref
        self.assertIn("bom-ref", cyclonedx["components"][0])
        
    def test_convert_to_cyclonedx_with_nested_components(self):
        """Test convert_to_cyclonedx with nested components."""
        # Sample repository info with submodules
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "submodule1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/submodule1.git",
                    "submodules": []
                }
            ]
        }

        # Convert to CycloneDX with use_nested_components=True
        cyclonedx = convert_to_cyclonedx(repo_info, use_nested_components=True)

        # Check the result
        self.assertEqual(cyclonedx["bomFormat"], "CycloneDX")
        self.assertEqual(cyclonedx["specVersion"], "1.4")
        self.assertIn("components", cyclonedx)
        self.assertEqual(len(cyclonedx["components"]), 1)  # Only the main repo at the top level
        
        # Should NOT have a dependencies section when use_nested_components=True
        self.assertNotIn("dependencies", cyclonedx)
        
        # Main component should have nested components
        main_component = cyclonedx["components"][0]
        self.assertIn("components", main_component)
        self.assertEqual(len(main_component["components"]), 1)  # One submodule
        
        # Check the nested component
        submodule = main_component["components"][0]
        self.assertEqual(submodule["name"], "submodule1")
        self.assertEqual(submodule["type"], "library")  # Submodules should always be "library" type

    def test_process_repo_as_component(self):
        """Test process_repo_as_component with a sample repository info."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Process as component (default: library for submodules)
        components = []
        process_repo_as_component(repo_info, components, is_main_repo=False)

        # Check the result
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["type"], "library")
        self.assertEqual(component["name"], "repo")
        self.assertEqual(component["version"], "abcdef12")
        self.assertEqual(component["purl"], "pkg:git/repo@abcdef1234567890")
        self.assertIn("properties", component)
        
        # Check for all expected properties
        property_names = [prop["name"] for prop in component["properties"]]
        self.assertIn("git:branch", property_names)
        self.assertIn("git:commit", property_names)
        self.assertIn("git:commit.short", property_names)
        self.assertIn("git:path", property_names)
        self.assertIn("git:worktree.path", property_names)
        self.assertIn("git:remote.url", property_names)
        self.assertIn("git:tag", property_names)
        
        # Check property values
        for prop in component["properties"]:
            if prop["name"] == "git:commit":
                self.assertEqual(prop["value"], "abcdef1234567890")
            elif prop["name"] == "git:commit.short":
                self.assertEqual(prop["value"], "abcdef12")
            elif prop["name"] == "git:remote.url":
                self.assertEqual(prop["value"], "https://github.com/user/repo.git")
        
        self.assertIn("externalReferences", component)
        self.assertEqual(len(component["externalReferences"]), 1)
        self.assertEqual(component["externalReferences"][0]["url"], "https://github.com/user/repo.git")
        
    def test_process_repo_as_component_main_repo(self):
        """Test process_repo_as_component with main repository flag."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Process as component with is_main_repo=True
        components = []
        process_repo_as_component(repo_info, components, is_main_repo=True)

        # Check the result
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["type"], "application")  # Should be application for main repo
        
    def test_process_repo_as_component_with_type_override(self):
        """Test process_repo_as_component with component_type override."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Process as component with component_type override
        components = []
        process_repo_as_component(repo_info, components, is_main_repo=True, component_type="framework")

        # Check the result
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["type"], "framework")  # Should use the override

    def test_process_repo_as_component_with_submodules(self):
        """Test process_repo_as_component with submodules."""
        # Sample repository info with submodules
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "module1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/module1.git",
                    "submodules": []
                }
            ]
        }

        # Process as component
        components = []
        dependencies = []  # Add dependencies list
        process_repo_as_component(repo_info, components, dependencies=dependencies, is_main_repo=True)

        # Check the result
        self.assertEqual(len(components), 2)  # Main repo and one submodule
        self.assertEqual(components[0]["name"], "repo")
        self.assertEqual(components[1]["name"], "module1")
        # Default types: application for main repo, library for submodule
        self.assertEqual(components[0]["type"], "application")
        self.assertEqual(components[1]["type"], "library")
        
        # Check dependencies
        self.assertEqual(len(dependencies), 1)  # One dependency entry for the main repo
        self.assertEqual(dependencies[0]["ref"], components[0]["bom-ref"])  # Main repo is the parent
        self.assertIn("dependsOn", dependencies[0])
        self.assertEqual(len(dependencies[0]["dependsOn"]), 1)  # Main repo depends on one submodule
        self.assertEqual(dependencies[0]["dependsOn"][0], components[1]["bom-ref"])  # Dependency is the submodule
        
    def test_process_repo_as_component_with_type_override_and_submodules(self):
        """Test that submodules remain 'library' type even when component_type is specified for main repo."""
        # Sample repository info with submodules
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "module1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/module1.git",
                    "submodules": []
                }
            ]
        }

        # Process as component with component_type override
        components = []
        dependencies = []  # Add dependencies list
        process_repo_as_component(repo_info, components, dependencies=dependencies, is_main_repo=True, component_type="firmware")

        # Check the result
        self.assertEqual(len(components), 2)  # Main repo and one submodule
        self.assertEqual(components[0]["name"], "repo")
        self.assertEqual(components[1]["name"], "module1")
        # Main repo should use the override type, but submodule should remain "library"
        self.assertEqual(components[0]["type"], "firmware")
        self.assertEqual(components[1]["type"], "library")
        
        # Check dependencies
        self.assertEqual(len(dependencies), 1)  # One dependency entry for the main repo
        self.assertEqual(dependencies[0]["ref"], components[0]["bom-ref"])  # Main repo is the parent
        self.assertIn("dependsOn", dependencies[0])
        self.assertEqual(len(dependencies[0]["dependsOn"]), 1)  # Main repo depends on one submodule
        self.assertEqual(dependencies[0]["dependsOn"][0], components[1]["bom-ref"])  # Dependency is the submodule
        
    def test_process_repo_as_nested_component(self):
        """Test process_repo_as_nested_component with a sample repository info."""
        # Sample repository info
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Process as nested component
        components = []
        process_repo_as_nested_component(repo_info, components, is_main_repo=True)

        # Check the result
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["type"], "application")  # Main repo should be application type by default
        self.assertEqual(component["name"], "repo")
        self.assertEqual(component["version"], "abcdef12")
        self.assertEqual(component["purl"], "pkg:git/repo@abcdef1234567890")
        self.assertIn("properties", component)
        
        # Should have a bom-ref (needed for validation compatibility)
        self.assertIn("bom-ref", component)
        self.assertEqual(component["bom-ref"], "pkg:git/repo@abcdef1234567890")
        
        # Should NOT have a components array since there are no submodules
        self.assertNotIn("components", component)
        
    def test_process_repo_as_nested_component_with_submodules(self):
        """Test process_repo_as_nested_component with submodules."""
        # Sample repository info with submodules
        repo_info = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "module1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/module1.git",
                    "submodules": []
                }
            ]
        }

        # Process as nested component
        components = []
        process_repo_as_nested_component(repo_info, components, is_main_repo=True)

        # Check the result
        self.assertEqual(len(components), 1)  # Only the main repo at the top level
        main_component = components[0]
        self.assertEqual(main_component["type"], "application")  # Main repo should be application type by default
        
        # Main component should have a bom-ref (needed for validation compatibility)
        self.assertIn("bom-ref", main_component)
        self.assertEqual(main_component["bom-ref"], "pkg:git/repo@abcdef1234567890")
        
        # Main component should have nested components
        self.assertIn("components", main_component)
        self.assertEqual(len(main_component["components"]), 1)  # One submodule
        
        # Check the nested component
        submodule = main_component["components"][0]
        self.assertEqual(submodule["name"], "module1")
        self.assertEqual(submodule["type"], "library")  # Submodules should always be "library" type
        
        # Submodule should also have a bom-ref (needed for validation compatibility)
        self.assertIn("bom-ref", submodule)
        self.assertEqual(submodule["bom-ref"], "pkg:git/module1@1234567890abcdef")


class TestCreateSbom(unittest.TestCase):
    """Tests for the create_sbom function."""

    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_returns_cyclonedx(self, mock_analyze):
        """Test that create_sbom returns a CycloneDX SBOM."""
        # Mock analyze_repo_recursive to return a sample repository info
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Call create_sbom
        repo_path = Path('.')
        sbom = create_sbom(repo_path)

        # Check the result
        self.assertIsInstance(sbom, dict)
        self.assertEqual(sbom["bomFormat"], "CycloneDX")
        self.assertEqual(sbom["specVersion"], "1.4")
        self.assertTrue(sbom["serialNumber"].startswith("urn:uuid:"))
        self.assertEqual(sbom["version"], 1)
        self.assertIn("metadata", sbom)
        self.assertIn("components", sbom)
        self.assertEqual(sbom["components"][0]["type"], "application")  # Default type for main repo
        mock_analyze.assert_called_once_with(".", ".")
        
    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_with_component_type(self, mock_analyze):
        """Test create_sbom with a custom component type."""
        # Mock analyze_repo_recursive to return a sample repository info
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Call create_sbom with custom component type
        repo_path = Path('.')
        sbom = create_sbom(repo_path, component_type="container")

        # Check the result
        self.assertEqual(sbom["components"][0]["type"], "container")
        
    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_with_component_type_and_submodules(self, mock_analyze):
        """Test create_sbom with a custom component type and submodules."""
        # Mock analyze_repo_recursive to return a sample repository info with submodules
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "module1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/module1.git",
                    "submodules": []
                }
            ]
        }

        # Call create_sbom with custom component type
        repo_path = Path('.')
        sbom = create_sbom(repo_path, component_type="operating-system")

        # Check the result
        self.assertEqual(len(sbom["components"]), 2)  # Main repo and one submodule
        # Main repo should use the specified type
        self.assertEqual(sbom["components"][0]["type"], "operating-system")
        # Submodule should remain "library" type regardless of component_type parameter
        self.assertEqual(sbom["components"][1]["type"], "library")
        # Should have a dependencies section by default
        self.assertIn("dependencies", sbom)
        
    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_with_nested_components(self, mock_analyze):
        """Test create_sbom with nested components."""
        # Mock analyze_repo_recursive to return a sample repository info with submodules
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://github.com/user/repo.git",
            "submodules": [
                {
                    "path": "module1",
                    "hash": "1234567890abcdef",
                    "branch": "main",
                    "tags": [],
                    "has_tag": False,
                    "url": "https://github.com/user/module1.git",
                    "submodules": []
                }
            ]
        }

        # Call create_sbom with use_nested_components=True
        repo_path = Path('.')
        sbom = create_sbom(repo_path, use_nested_components=True)

        # Check the result
        self.assertEqual(len(sbom["components"]), 1)  # Only the main repo at the top level
        
        # Should NOT have a dependencies section when use_nested_components=True
        self.assertNotIn("dependencies", sbom)
        
        # Main component should have nested components
        main_component = sbom["components"][0]
        
        # Main component should have a bom-ref (needed for validation compatibility)
        self.assertIn("bom-ref", main_component)
        self.assertEqual(main_component["bom-ref"], "pkg:git/repo@abcdef1234567890")
        
        self.assertIn("components", main_component)
        self.assertEqual(len(main_component["components"]), 1)  # One submodule
        
        # Check the nested component
        submodule = main_component["components"][0]
        self.assertEqual(submodule["name"], "module1")
        self.assertEqual(submodule["type"], "library")  # Submodules should always be "library" type
        
        # Submodule should also have a bom-ref (needed for validation compatibility)
        self.assertIn("bom-ref", submodule)
        self.assertEqual(submodule["bom-ref"], "pkg:git/module1@1234567890abcdef")

    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_with_output_path(self, mock_analyze):
        """Test create_sbom with an output path."""
        # Mock analyze_repo_recursive to return a sample repository info
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Call create_sbom with the temporary file as output
            repo_path = Path('.')
            sbom = create_sbom(repo_path, temp_path, component_type="library")

            # Check that the file was created and contains valid JSON
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                file_content = json.load(f)
                self.assertEqual(file_content["bomFormat"], "CycloneDX")
                self.assertEqual(file_content["components"][0]["type"], "library")
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_error_handling(self, mock_analyze):
        """Test error handling in create_sbom."""
        # Mock analyze_repo_recursive to raise an exception
        mock_analyze.side_effect = ValueError("Test error")

        # Call create_sbom with a component type and print_errors=False to suppress error messages
        repo_path = Path('.')
        sbom = create_sbom(repo_path, component_type="firmware", print_errors=False)

        # Check that an error SBOM is returned
        self.assertIsInstance(sbom, dict)
        self.assertEqual(sbom["bomFormat"], "CycloneDX")
        self.assertEqual(sbom["specVersion"], "1.4")
        self.assertEqual(len(sbom["components"]), 0)
        self.assertIn("errors", sbom)
        self.assertEqual(sbom["errors"][0], "Test error")
        
        # Check that the metadata component has the correct type
        self.assertIn("metadata", sbom)
        self.assertIn("component", sbom["metadata"])
        self.assertEqual(sbom["metadata"]["component"]["type"], "firmware")
        
    @mock.patch('sbom_git_sm.main.analyze_repo_recursive')
    def test_create_sbom_with_nonexistent_output_directory(self, mock_analyze):
        """Test create_sbom with an output path where parent directories don't exist."""
        # Mock analyze_repo_recursive to return a sample repository info
        mock_analyze.return_value = {
            "path": "/path/to/repo",
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": ["v1.0.0"],
            "has_tag": True,
            "url": "https://github.com/user/repo.git",
            "submodules": []
        }

        # Create a temporary base directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define an output path with non-existent subdirectories
            base_dir = Path(temp_dir)
            nonexistent_dir = base_dir / "subdir1" / "subdir2"
            output_path = nonexistent_dir / "sbom_output.json"
            
            try:
                # Verify that the directory doesn't exist yet
                self.assertFalse(nonexistent_dir.exists())
                
                # Call create_sbom with the output path
                repo_path = Path('.')
                sbom = create_sbom(repo_path, output_path)
                
                # Check that the directories were created
                self.assertTrue(nonexistent_dir.exists())
                
                # Check that the file was created and contains valid JSON
                self.assertTrue(output_path.exists())
                with open(output_path, 'r') as f:
                    file_content = json.load(f)
                    self.assertEqual(file_content["bomFormat"], "CycloneDX")
            finally:
                # Clean up the file if it exists
                if output_path.exists():
                    output_path.unlink()


# Note: For integration testing, a real Git repository with submodules is needed.
# This could be set up in a CI/CD pipeline or manually for local testing.
# The following test is commented out as it requires a real Git repository.
"""
class TestIntegration(unittest.TestCase):
    def test_with_real_repository(self):
        # This test requires a real Git repository with submodules
        # It should be run in an environment where such a repository is available
        repo_path = Path('/path/to/test/repo')
        sbom = create_sbom(repo_path)
        
        # Verify the SBOM structure and content
        self.assertEqual(sbom["bomFormat"], "CycloneDX")
        # Additional assertions based on the expected repository structure
"""


class TestVersionExtraction(unittest.TestCase):
    """Tests for version extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        
        # Create a test JSON configuration file
        self.json_config = {
            "main": {
                "file_pattern": "version.txt",
                "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
            },
            "submodules": [
                {
                    "name_pattern": "TestSub1",
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                },
                {
                    "name_pattern": ".*",
                    "file_pattern": "*.txt",
                    "regex_pattern": r"([0-9]+\.[0-9]+\.[0-9]+)"
                }
            ]
        }
        
        self.json_config_path = os.path.join(self.temp_dir.name, "version_config.json")
        with open(self.json_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.json_config, f)
        
        # Create a test version file for the main repository
        self.main_version_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(self.main_version_path, 'w', encoding='utf-8') as f:
            f.write('version = "1.2.3"')
        
        # Create a test version file for a submodule
        os.makedirs(os.path.join(self.temp_dir.name, "TestSub1"), exist_ok=True)
        self.sub1_version_path = os.path.join(self.temp_dir.name, "TestSub1", "version.txt")
        with open(self.sub1_version_path, 'w', encoding='utf-8') as f:
            f.write('version = "4.5.6"')
        
        # Create a test version file for another submodule
        os.makedirs(os.path.join(self.temp_dir.name, "TestSub2"), exist_ok=True)
        self.sub2_version_path = os.path.join(self.temp_dir.name, "TestSub2", "info.txt")
        with open(self.sub2_version_path, 'w', encoding='utf-8') as f:
            f.write('This is version 7.8.9 of the software')
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_get_repo_info_with_version_config(self, mock_run):
        """Test get_repo_info with version configuration."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Get repository information
        repo_info = get_repo_info(self.temp_dir.name, self.temp_dir.name, version_config)
        
        # Check that the version was extracted from the file
        self.assertEqual(repo_info["version"], "1.2.3")
        self.assertEqual(repo_info["version_source"], "file")
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_get_repo_info_fallback_to_hash(self, mock_run):
        """Test get_repo_info fallback to hash when version can't be extracted."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Remove the version file
        os.remove(self.main_version_path)
        
        # Get repository information
        repo_info = get_repo_info(self.temp_dir.name, self.temp_dir.name, version_config)
        
        # Check that the version fallback to hash
        self.assertEqual(repo_info["version"], "abcdef12")
        self.assertEqual(repo_info["version_source"], "hash")
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    @mock.patch('sbom_git_sm.main.warnings.warn')
    def test_get_repo_info_detailed_warning(self, mock_warn, mock_run):
        """Test that get_repo_info includes detailed error message in warning."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Create a test file that doesn't match the regex pattern
        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('This file does not contain a version')
        
        # Get repository information
        repo_info = get_repo_info(self.temp_dir.name, self.temp_dir.name, version_config)
        
        # Check that the version fallback to hash
        self.assertEqual(repo_info["version"], "abcdef12")
        self.assertEqual(repo_info["version_source"], "hash")
        
        # Check that the warning was issued with the detailed error message
        mock_warn.assert_called_once()
        warning_message = mock_warn.call_args[0][0]
        self.assertIn("Could not extract version for main repository using configuration", warning_message)
        self.assertIn("Regex pattern", warning_message)
        self.assertIn("did not match content", warning_message)
        
    @mock.patch('sbom_git_sm.main.subprocess.run')
    @mock.patch('sbom_git_sm.main.warnings.warn')
    def test_get_repo_info_submodule_detailed_warning(self, mock_warn, mock_run):
        """Test that get_repo_info includes detailed error message in warning for submodules."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Create a test file for submodule that doesn't match the regex pattern
        os.makedirs(os.path.join(self.temp_dir.name, "TestSub1"), exist_ok=True)
        test_file_path = os.path.join(self.temp_dir.name, "TestSub1", "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('This file does not contain a version')
        
        # Get repository information for a submodule
        # Use a different path for root_path to make it a submodule
        repo_info = get_repo_info(os.path.join(self.temp_dir.name, "TestSub1"), self.temp_dir.name, version_config)
        
        # Check that the version fallback to hash
        self.assertEqual(repo_info["version"], "abcdef12")
        self.assertEqual(repo_info["version_source"], "hash")
        
        # Check that the warning was issued with the detailed error message
        mock_warn.assert_called_once()
        warning_message = mock_warn.call_args[0][0]
        self.assertIn("Could not extract version for submodule 'TestSub1' using configuration", warning_message)
        self.assertIn("Regex pattern", warning_message)
        self.assertIn("did not match content", warning_message)

    @mock.patch('sbom_git_sm.main.subprocess.run')
    @mock.patch('sbom_git_sm.main.warnings.warn')
    def test_get_repo_info_submodule_name_mismatch_hint(self, mock_warn, mock_run):
        """Test warning when config matches .gitmodules name but not folder name."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0

        mismatch_config = {
            "submodules": [
                {
                    "name_pattern": "PrettySubmodule",
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                }
            ]
        }
        config_path = os.path.join(self.temp_dir.name, "mismatch_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(mismatch_config, f)

        version_config = VersionConfig(config_path)

        submodule_path = os.path.join(self.temp_dir.name, "FolderName")
        os.makedirs(submodule_path, exist_ok=True)

        repo_info = get_repo_info(
            submodule_path,
            self.temp_dir.name,
            version_config,
            submodule_name="PrettySubmodule"
        )

        self.assertEqual(repo_info["version"], "abcdef12")
        mock_warn.assert_called_once()
        warning_message = mock_warn.call_args[0][0]
        self.assertIn("folder name", warning_message)
        self.assertIn("PrettySubmodule", warning_message)
        self.assertIn("FolderName", warning_message)
        
    @mock.patch('sbom_git_sm.main.subprocess.run')
    @mock.patch('sbom_git_sm.main.os.getcwd')
    def test_get_repo_info_with_different_root_path(self, mock_getcwd, mock_run):
        """Test get_repo_info with a different root path than the current working directory."""
        # Mock os.getcwd to return a different directory
        mock_getcwd.return_value = "/different/working/directory"
        
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Get repository information with a specific root path
        repo_path = self.temp_dir.name
        root_path = repo_path  # Specify that this is the root repository
        
        # Get repository information
        repo_info = get_repo_info(repo_path, root_path, version_config)
        
        # Check that the version was extracted from the file (main repository config was used)
        self.assertEqual(repo_info["version"], "1.2.3")
        self.assertEqual(repo_info["version_source"], "file")
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    @mock.patch('sbom_git_sm.main.is_git_repo')
    @mock.patch('sbom_git_sm.main.get_submodules')
    def test_analyze_repo_recursive_with_version_config(self, mock_get_submodules, mock_is_git_repo, mock_run):
        """Test analyze_repo_recursive with version configuration."""
        # Mock is_git_repo to return True
        mock_is_git_repo.return_value = True
        
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Mock get_submodules to return test submodules
        mock_get_submodules.return_value = [
            {"name": "TestSub1", "path": "TestSub1", "url": "https://example.com/TestSub1"},
            {"name": "TestSub2", "path": "TestSub2", "url": "https://example.com/TestSub2"}
        ]
        
        # Create version configuration
        version_config = VersionConfig(self.json_config_path)
        
        # Analyze repository recursively
        repo_info = analyze_repo_recursive(self.temp_dir.name, self.temp_dir.name, version_config)
        
        # Check that the main repository version was extracted from the file
        self.assertEqual(repo_info["version"], "1.2.3")
        self.assertEqual(repo_info["version_source"], "file")
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_process_repo_as_component_with_version_source(self, mock_run):
        """Test process_repo_as_component with version source property."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create repository information with version source
        repo_info = {
            "path": self.temp_dir.name,
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://example.com/repo",
            "submodules": [],
            "name": "repo",
            "version": "1.2.3",
            "version_source": "file"
        }
        
        # Process repository as component
        components = []
        process_repo_as_component(repo_info, components, is_main_repo=True)
        
        # Check that the component has the version source property
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["version"], "1.2.3")
        
        # Find the version source property
        version_source_prop = next((p for p in component["properties"] if p["name"] == "version:source"), None)
        self.assertIsNotNone(version_source_prop)
        self.assertEqual(version_source_prop["value"], "file")
    
    @mock.patch('sbom_git_sm.main.subprocess.run')
    def test_process_repo_as_nested_component_with_version_source(self, mock_run):
        """Test process_repo_as_nested_component with version source property."""
        # Mock subprocess.run to return git information
        mock_run.return_value.stdout = "abcdef1234567890\n"
        mock_run.return_value.returncode = 0
        
        # Create repository information with version source
        repo_info = {
            "path": self.temp_dir.name,
            "hash": "abcdef1234567890",
            "branch": "main",
            "tags": [],
            "has_tag": False,
            "url": "https://example.com/repo",
            "submodules": [],
            "name": "repo",
            "version": "1.2.3",
            "version_source": "file"
        }
        
        # Process repository as nested component
        components = []
        process_repo_as_nested_component(repo_info, components, is_main_repo=True)
        
        # Check that the component has the version source property
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component["version"], "1.2.3")
        
        # Find the version source property
        version_source_prop = next((p for p in component["properties"] if p["name"] == "version:source"), None)
        self.assertIsNotNone(version_source_prop)
        self.assertEqual(version_source_prop["value"], "file")


if __name__ == '__main__':
    unittest.main()
