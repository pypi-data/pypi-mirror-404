"""
Unit tests for the version_config module.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.
"""

import os
import json
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

from sbom_git_sm.version_config import VersionConfig, YAML_AVAILABLE

# Skip YAML tests if PyYAML is not available
SKIP_YAML_TESTS = not YAML_AVAILABLE


class TestVersionConfig(unittest.TestCase):
    """Test the VersionConfig class."""
    
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
        
        # Create a test YAML configuration file if PyYAML is available
        if YAML_AVAILABLE:
            import yaml
            self.yaml_config = {
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
            
            self.yaml_config_path = os.path.join(self.temp_dir.name, "version_config.yaml")
            with open(self.yaml_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.yaml_config, f)
    
    def test_load_json_config(self):
        """Test loading a JSON configuration file."""
        config = VersionConfig(self.json_config_path)
        
        # Check that the configuration was loaded correctly
        self.assertEqual(config.config, self.json_config)
        
        # Check that the main configuration was parsed correctly
        main_config = config.get_main_config()
        self.assertEqual(main_config, self.json_config["main"])
        
        # Check that the submodule configurations were parsed correctly
        submodule_config = config.get_submodule_config("TestSub1")
        self.assertEqual(submodule_config, self.json_config["submodules"][0])
        
        # Check that the wildcard pattern works
        submodule_config = config.get_submodule_config("TestSub2")
        self.assertEqual(submodule_config, self.json_config["submodules"][1])
    
    @unittest.skipIf(SKIP_YAML_TESTS, "PyYAML not available")
    def test_load_yaml_config(self):
        """Test loading a YAML configuration file."""
        config = VersionConfig(self.yaml_config_path)
        
        # Check that the configuration was loaded correctly
        self.assertEqual(config.config, self.yaml_config)
        
        # Check that the main configuration was parsed correctly
        main_config = config.get_main_config()
        self.assertEqual(main_config, self.yaml_config["main"])
        
        # Check that the submodule configurations were parsed correctly
        submodule_config = config.get_submodule_config("TestSub1")
        self.assertEqual(submodule_config, self.yaml_config["submodules"][0])
        
        # Check that the wildcard pattern works
        submodule_config = config.get_submodule_config("TestSub2")
        self.assertEqual(submodule_config, self.yaml_config["submodules"][1])

    @unittest.skipIf(SKIP_YAML_TESTS, "PyYAML not available")
    def test_yaml_unquoted_hash_regex_pattern(self):
        """Test YAML regex pattern with unquoted # is handled with a clear error."""
        yaml_path = os.path.join(self.temp_dir.name, "unquoted_hash.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(
                "main:\n"
                "  file_pattern: version.txt\n"
                "  regex_pattern: #define\\s+Version\\s+\"([0-9]+\\.[0-9]+\\.[0-9]+)\"\n"
            )

        config = VersionConfig(yaml_path)
        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('#define Version "1.2.3"')

        main_config = config.get_main_config()
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("Not a string", error_message)
        self.assertIn("YAML", error_message)

    def test_extract_version(self):
        """Test extracting a version from a file using a configuration."""
        config = VersionConfig(self.json_config_path)
        
        # Create a test file with a version
        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('version = "1.2.3"')
        
        # Extract the version using the main configuration
        main_config = config.get_main_config()
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertEqual(version, "1.2.3")
        self.assertIsNone(error_message)
        
        # Create a test file with a different format
        test_file2_path = os.path.join(self.temp_dir.name, "version2.txt")
        with open(test_file2_path, 'w', encoding='utf-8') as f:
            f.write('This is version 4.5.6 of the software')
        
        # Extract the version using the wildcard configuration
        wildcard_config = config.get_submodule_config("TestSub2")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            version, error_message = config.extract_version(self.temp_dir.name, wildcard_config)
        self.assertEqual(version, "1.2.3")
        self.assertIsNone(error_message)
        self.assertTrue(any("Multiple version matches found" in str(w.message) for w in caught))
    
    def test_extract_version_not_found(self):
        """Test extracting a version when it can't be found."""
        config = VersionConfig(self.json_config_path)
        
        # Create a test file without a version
        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('This file does not contain a version')
        
        # Extract the version using the main configuration
        main_config = config.get_main_config()
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("Regex pattern", error_message)
        self.assertIn("did not match content", error_message)

    def test_extract_version_no_capture_group(self):
        """Test extracting a version when regex has no capturing group."""
        config = VersionConfig(self.json_config_path)

        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('version = "1.2.3"')

        main_config = config.get_main_config()
        main_config["regex_pattern"] = r"version\s*=\s*['\"][0-9]+\.[0-9]+\.[0-9]+['\"]"
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("no capturing group 1", error_message)

    def test_extract_version_empty_capture_group(self):
        """Test extracting a version when capture group is empty."""
        config = VersionConfig(self.json_config_path)

        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('version = ""')

        main_config = config.get_main_config()
        main_config["regex_pattern"] = r"version\s*=\s*['\"]([^'\"]*)['\"]"
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("capturing group 1 was empty", error_message)

    def test_extract_version_utf16_with_bom(self):
        """Test extracting a version from a UTF-16 file with BOM."""
        config = VersionConfig(self.json_config_path)

        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-16') as f:
            f.write('version = "1.2.3"')

        main_config = config.get_main_config()
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertEqual(version, "1.2.3")
        self.assertIsNone(error_message)

    def test_extract_version_encoding_hint_on_decode_error(self):
        """Test hint on decode error when encoding is misconfigured."""
        config = VersionConfig(self.json_config_path)

        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('version = "1.2.3"\n# Gr\u00fc\u00dfe')

        main_config = config.get_main_config()
        main_config["encoding"] = "ascii"
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("Hint: set 'encoding'", error_message)

    def test_extract_version_multiple_matches_warns_and_uses_first(self):
        """Test multiple matches: warning emitted and first match used."""
        config = VersionConfig(self.json_config_path)

        file_a = os.path.join(self.temp_dir.name, "a.txt")
        file_b = os.path.join(self.temp_dir.name, "b.txt")
        with open(file_a, 'w', encoding='utf-8') as f:
            f.write('This is version 1.2.3 of the software')
        with open(file_b, 'w', encoding='utf-8') as f:
            f.write('This is version 2.0.0 of the software')

        wildcard_config = config.get_submodule_config("TestSub2")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            version, error_message = config.extract_version(self.temp_dir.name, wildcard_config)

        self.assertEqual(version, "1.2.3")
        self.assertIsNone(error_message)
        self.assertTrue(any("Multiple version matches found" in str(w.message) for w in caught))
        warning_message = next(
            str(w.message) for w in caught if "Multiple version matches found" in str(w.message)
        )
        self.assertIn("1.2.3", warning_message)
        self.assertIn("2.0.0", warning_message)
        self.assertIn("a.txt", warning_message)
        self.assertIn("b.txt", warning_message)

    def test_extract_version_with_recursive_glob(self):
        """Test extracting a version with ** recursive glob pattern."""
        config = VersionConfig(self.json_config_path)

        nested_dir = os.path.join(self.temp_dir.name, "subdir", "inner")
        os.makedirs(nested_dir, exist_ok=True)
        nested_file = os.path.join(nested_dir, "version.txt")
        with open(nested_file, 'w', encoding='utf-8') as f:
            f.write('version = "9.8.7"')

        main_config = config.get_main_config()
        main_config["file_pattern"] = "**/version.txt"
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertEqual(version, "9.8.7")
        self.assertIsNone(error_message)

    def test_extract_version_excludes_submodule_paths(self):
        """Test that files under .gitmodules paths are excluded from matching."""
        config = VersionConfig(self.json_config_path)

        gitmodules_path = os.path.join(self.temp_dir.name, ".gitmodules")
        with open(gitmodules_path, 'w', encoding='utf-8') as f:
            f.write('[submodule "Sub1"]\n')
            f.write('\tpath = sub1\n')
            f.write('\turl = https://example.com/Sub1.git\n')

        root_version = os.path.join(self.temp_dir.name, "version.txt")
        with open(root_version, 'w', encoding='utf-8') as f:
            f.write('version = "1.0.0"')

        sub_dir = os.path.join(self.temp_dir.name, "sub1")
        os.makedirs(sub_dir, exist_ok=True)
        sub_version = os.path.join(sub_dir, "version.txt")
        with open(sub_version, 'w', encoding='utf-8') as f:
            f.write('version = "2.0.0"')

        main_config = config.get_main_config()
        main_config["file_pattern"] = "**/version.txt"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            version, error_message = config.extract_version(self.temp_dir.name, main_config)

        self.assertEqual(version, "1.0.0")
        self.assertIsNone(error_message)
        self.assertFalse(any("Multiple version matches found" in str(w.message) for w in caught))

    def test_extract_version_excludes_nested_submodule_paths(self):
        """Test exclusion works for submodules of submodules."""
        config = VersionConfig(self.json_config_path)

        sub_repo = os.path.join(self.temp_dir.name, "sub1")
        nested_repo = os.path.join(sub_repo, "nested")
        os.makedirs(nested_repo, exist_ok=True)

        gitmodules_path = os.path.join(sub_repo, ".gitmodules")
        with open(gitmodules_path, 'w', encoding='utf-8') as f:
            f.write('[submodule "Nested"]\n')
            f.write('\tpath = nested\n')
            f.write('\turl = https://example.com/Nested.git\n')

        sub_version = os.path.join(sub_repo, "version.txt")
        with open(sub_version, 'w', encoding='utf-8') as f:
            f.write('version = "3.0.0"')

        nested_version = os.path.join(nested_repo, "version.txt")
        with open(nested_version, 'w', encoding='utf-8') as f:
            f.write('version = "9.9.9"')

        main_config = config.get_main_config()
        main_config["file_pattern"] = "**/version.txt"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            version, error_message = config.extract_version(sub_repo, main_config)

        self.assertEqual(version, "3.0.0")
        self.assertIsNone(error_message)
        self.assertFalse(any("Multiple version matches found" in str(w.message) for w in caught))

    def test_extract_version_file_not_found(self):
        """Test extracting a version when the file can't be found."""
        config = VersionConfig(self.json_config_path)
        
        # Extract the version using the main configuration
        main_config = config.get_main_config()
        main_config["file_pattern"] = "nonexistent.txt"
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("No files matching pattern", error_message)
    
    def test_extract_version_invalid_regex(self):
        """Test extracting a version with an invalid regex pattern."""
        config = VersionConfig(self.json_config_path)
        
        # Create a test file with a version
        test_file_path = os.path.join(self.temp_dir.name, "version.txt")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('version = "1.2.3"')
        
        # Extract the version using a configuration with an invalid regex
        main_config = config.get_main_config()
        main_config["regex_pattern"] = "("  # Invalid regex (unclosed group)
        version, error_message = config.extract_version(self.temp_dir.name, main_config)
        self.assertIsNone(version)
        self.assertIsNotNone(error_message)
        self.assertIn("Invalid regex pattern", error_message)
    
    def test_invalid_config_path(self):
        """Test loading a configuration from an invalid path."""
        with self.assertRaises(ValueError):
            VersionConfig("nonexistent.json")
    
    def test_unsupported_config_format(self):
        """Test loading a configuration with an unsupported format."""
        # Create a file with an unsupported extension
        unsupported_path = os.path.join(self.temp_dir.name, "config.txt")
        with open(unsupported_path, 'w', encoding='utf-8') as f:
            f.write('This is not a valid configuration file')
        
        with self.assertRaises(ValueError):
            VersionConfig(unsupported_path)

    def test_null_json_config(self):
        """Test loading a JSON config that parses to null."""
        null_json_path = os.path.join(self.temp_dir.name, "null_config.json")
        with open(null_json_path, 'w', encoding='utf-8') as f:
            f.write('null')

        with self.assertRaises(ValueError) as ctx:
            VersionConfig(null_json_path)
        self.assertIn("empty or invalid", str(ctx.exception).lower())

    @unittest.skipIf(SKIP_YAML_TESTS, "PyYAML not available")
    def test_empty_yaml_config(self):
        """Test loading an empty YAML config."""
        empty_yaml_path = os.path.join(self.temp_dir.name, "empty_config.yaml")
        with open(empty_yaml_path, 'w', encoding='utf-8') as f:
            f.write('')

        with self.assertRaises(ValueError) as ctx:
            VersionConfig(empty_yaml_path)
        self.assertIn("empty or invalid", str(ctx.exception).lower())

    def test_invalid_name_pattern_type(self):
        """Test that non-string name_pattern does not crash parsing."""
        invalid_pattern_config = {
            "submodules": [
                {
                    "name_pattern": 123,
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                },
                {
                    "name_pattern": "ValidSub",
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                }
            ]
        }
        invalid_config_path = os.path.join(self.temp_dir.name, "invalid_name_pattern.json")
        with open(invalid_config_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_pattern_config, f)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            config = VersionConfig(invalid_config_path)

        self.assertIsNotNone(config)
        self.assertEqual(config.get_submodule_config("ValidSub"), invalid_pattern_config["submodules"][1])
        self.assertTrue(any("Invalid regex pattern" in str(w.message) for w in caught))

    def test_get_submodule_config_match_semantics(self):
        """Test that name_pattern uses match (start-anchored), not search."""
        match_config = {
            "submodules": [
                {
                    "name_pattern": "module",
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                },
                {
                    "name_pattern": ".*module.*",
                    "file_pattern": "version.txt",
                    "regex_pattern": r"version\s*=\s*['\"]([^'\"]+)['\"]"
                }
            ]
        }
        match_config_path = os.path.join(self.temp_dir.name, "match_semantics.json")
        with open(match_config_path, 'w', encoding='utf-8') as f:
            json.dump(match_config, f)

        config = VersionConfig(match_config_path)
        selected = config.get_submodule_config("SubmoduleName")
        self.assertEqual(selected, match_config["submodules"][1])


if __name__ == '__main__':
    unittest.main()
