"""
Version configuration module for sbom-git-sm.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.

This module provides functionality for loading and parsing version configuration files.
"""

import codecs
import configparser
import json
import os
import re
import glob
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional, Pattern, Union, Tuple

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class VersionConfig:
    """Class for handling version configuration."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the version configuration.
        
        Args:
            config_path: Path to the configuration file (JSON or YAML)
        """
        self.config = {}
        self.main_config = None
        self.submodule_configs = []
        self.compiled_patterns = []
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file (JSON or YAML)
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ValueError: If the file format is not supported or the file cannot be parsed
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ValueError(f"Configuration file not found: {config_path}")
        
        # Determine file format based on extension
        file_ext = config_path.suffix.lower()
        
        if file_ext == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        elif file_ext in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ValueError("YAML support requires PyYAML. Install it with 'pip install PyYAML'")

            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")

        if self.config is None:
            raise ValueError("Configuration file is empty or invalid (parsed to null).")

        if not isinstance(self.config, dict):
            raise ValueError(
                f"Configuration file must contain a mapping/object at the top level, got {type(self.config).__name__}."
            )
        
        # Parse the configuration
        self._parse_config()
        
        return self.config
    
    def _parse_config(self):
        """Parse the loaded configuration and compile regex patterns."""
        # Parse main repository configuration
        if 'main' in self.config:
            self.main_config = self.config['main']
        
        # Parse submodule configurations
        if 'submodules' in self.config and isinstance(self.config['submodules'], list):
            self.submodule_configs = self.config['submodules']
            
            # Compile regex patterns for submodule name matching
            self.compiled_patterns = []
            for config in self.submodule_configs:
                if 'name_pattern' in config:
                    try:
                        pattern = re.compile(config['name_pattern'])
                        self.compiled_patterns.append((pattern, config))
                    except (re.error, TypeError) as e:
                        warnings.warn(f"Invalid regex pattern '{config['name_pattern']}': {e}")
    
    def get_main_config(self) -> Optional[Dict[str, str]]:
        """
        Get the configuration for the main repository.
        
        Returns:
            Dictionary containing the configuration or None if not configured
        """
        return self.main_config
    
    def get_submodule_config(self, submodule_name: str) -> Optional[Dict[str, str]]:
        """
        Get the configuration for a submodule based on its name.
        
        Args:
            submodule_name: Name of the submodule
            
        Returns:
            Dictionary containing the configuration or None if no matching configuration
        """
        for pattern, config in self.compiled_patterns:
            if pattern.match(submodule_name):
                return config
        
        return None
    
    def extract_version(self, repo_path: str, config: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract version from a file using the provided configuration.
        
        This method attempts to extract a version from files in the repository using the
        provided configuration. If extraction fails, it returns a detailed error message
        explaining why, which can be one of:
        - "No files matching pattern '{file_pattern}' found in '{repo_path}'"
        - "Invalid regex pattern '{regex_pattern}': {error}"
        - "Regex pattern '{regex_pattern}' did not match content in '{file_path}'"
        - "Regex pattern '{regex_pattern}' matched content in '{file_path}' but has no capturing group 1"
        - "Regex pattern '{regex_pattern}' matched content in '{file_path}' but capturing group 1 was empty"
        - "Regex pattern '{regex_pattern}' matched content in '{file_path}' but capturing group 1 was not set"
        - "Error reading file '{file_path}': {error}"

        If multiple files match the regex with a valid version, a warning is emitted listing
        all matches and the first match (by deterministic file order) is used.
        
        Note for YAML configuration files:
        If your regex pattern contains special characters like '#', make sure to enclose
        the pattern in quotes to prevent YAML from interpreting it as a comment:
        
        ```yaml
        regex_pattern: "#define\\s+Version\\s+\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
        ```
        
        Note on string formatting:
        Error messages in this method are built with f-strings and are safe to use in warnings.
        
        Args:
            repo_path: Path to the repository
            config: Configuration dictionary with file_pattern and regex_pattern
            
        Returns:
            A tuple of (extracted_version, error_message) where:
            - extracted_version: The extracted version string or None if not found
            - error_message: A detailed error message explaining why extraction failed, or None if successful
        """
        if not config or 'file_pattern' not in config or 'regex_pattern' not in config:
            return None, "Invalid configuration: missing file_pattern or regex_pattern"
        
        file_pattern = config['file_pattern']
        regex_pattern = config['regex_pattern']
        encoding = config.get('encoding')
        
        try:
            # Find files matching the pattern
            pattern_path = os.path.join(repo_path, file_pattern)
            matching_files = glob.glob(pattern_path, recursive=True)

            # Exclude paths from .gitmodules (submodule directories)
            gitmodules_path = os.path.join(repo_path, ".gitmodules")
            if os.path.isfile(gitmodules_path):
                parser = configparser.RawConfigParser()
                parser.optionxform = str
                try:
                    parser.read(gitmodules_path, encoding="utf-8")
                    exclude_dirs = []
                    for section in parser.sections():
                        if parser.has_option(section, "path"):
                            sub_path = parser.get(section, "path")
                            abs_path = os.path.normcase(os.path.abspath(os.path.join(repo_path, sub_path)))
                            exclude_dirs.append(abs_path)

                    if exclude_dirs:
                        filtered = []
                        for file_path in matching_files:
                            norm_path = os.path.normcase(os.path.abspath(file_path))
                            if any(
                                norm_path == ex_dir or norm_path.startswith(ex_dir + os.sep)
                                for ex_dir in exclude_dirs
                            ):
                                continue
                            filtered.append(file_path)
                        matching_files = filtered
                except Exception:
                    # If .gitmodules cannot be parsed, proceed without exclusions.
                    pass
            
            # Check if any files were found
            if not matching_files:
                return None, f"No files matching pattern '{file_pattern}' found in '{repo_path}'"

            # Use deterministic path order to define the "first" match.
            matching_files = sorted(matching_files)
            
            # Check if regex_pattern is a string (important for YAML files with unquoted # characters)
            if not isinstance(regex_pattern, str):
                return None, "Invalid regex pattern: Not a string. For YAML files, ensure patterns with special characters like '#' are enclosed in quotes."
            
            # Check for common YAML issues with # character
            if regex_pattern.startswith('#') and 'yaml' in str(self.config).lower():
                return None, "Invalid regex pattern starting with '#'. In YAML files, patterns with '#' must be enclosed in quotes like: \"#define\\\\s+Version\\\\s+\\\"([0-9]+\\\\.[0-9]+\\\\.[0-9]+)\\\"\""
            
            # Compile regex pattern
            try:
                regex = re.compile(regex_pattern)
            except re.error as e:
                return None, f"Invalid regex pattern '{regex_pattern}': {e}"
            
            # Try to extract version from each matching file
            file_errors = []
            version_matches = []
            for file_path in matching_files:
                try:
                    if encoding:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                    else:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            with open(file_path, 'rb') as f:
                                raw = f.read()

                            bom_encoding = None
                            if raw.startswith(codecs.BOM_UTF8):
                                bom_encoding = 'utf-8-sig'
                            elif raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
                                bom_encoding = 'utf-32'
                            elif raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
                                bom_encoding = 'utf-16'

                            if not bom_encoding:
                                raise ValueError("Unable to decode as UTF-8 and no supported BOM was found")

                            content = raw.decode(bom_encoding)
                    
                    match = regex.search(content)
                    if match:
                        if regex.groups < 1:
                            file_errors.append(
                                f"Regex pattern '{regex_pattern}' matched content in '{file_path}' but has no capturing group 1"
                            )
                            continue

                        group1 = match.group(1)
                        if group1 is None:
                            file_errors.append(
                                f"Regex pattern '{regex_pattern}' matched content in '{file_path}' but capturing group 1 was not set"
                            )
                        elif group1 == "":
                            file_errors.append(
                                f"Regex pattern '{regex_pattern}' matched content in '{file_path}' but capturing group 1 was empty"
                            )
                        else:
                            version_matches.append((file_path, group1))
                    else:
                        file_errors.append(f"Regex pattern '{regex_pattern}' did not match content in '{file_path}'")
                except (UnicodeDecodeError, ValueError, LookupError) as e:
                    file_errors.append(
                        f"Error reading file '{file_path}': {e}. "
                        "Hint: set 'encoding' in your version configuration to match the file encoding."
                    )
                except Exception as e:
                    file_errors.append(f"Error reading file '{file_path}': {e}")

            if version_matches:
                if len(version_matches) > 1:
                    matches_text = ", ".join(
                        f"{version} in '{path}'" for path, version in version_matches
                    )
                    warnings.warn(
                        "Multiple version matches found; using the first match. "
                        f"Matches: {matches_text}"
                    )
                return version_matches[0][1], None
            
            # If we got here, no version was found in any of the files
            if len(matching_files) == 1:
                return None, file_errors[0]
            else:
                return None, f"No version found in {len(matching_files)} matching files: {', '.join(file_errors)}"
        
        except Exception as e:
            return None, f"Error extracting version: {e}"
