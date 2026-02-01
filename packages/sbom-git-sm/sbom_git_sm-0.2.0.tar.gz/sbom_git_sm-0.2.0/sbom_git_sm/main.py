"""
Main module for sbom-git-sm.

Copyright (c) 2025-2026 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.

This module provides the core functionality for creating a Software Bill of Materials (SBOM)
from a git repository based on its submodules.
"""

import json
import os
import re
import subprocess
import sys
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Use package-level version
from . import __version__


def strip_username_from_url(url: str) -> str:
    """
    Strip username from a URL if present.
    
    Args:
        url: URL that might contain a username
        
    Returns:
        URL with username removed
    """
    if not url:
        return url
        
    # Match pattern like https://username@domain or http://username@domain
    pattern = r'^(https?://)([^@:]+@)(.+)$'
    return re.sub(pattern, r'\1\3', url)


def add_version_source_property(component: Dict[str, Any], repo_info: Dict[str, Any]):
    """
    Add version source property to a component if available in repo_info.
    
    Args:
        component: Component dictionary to add property to
        repo_info: Repository information dictionary
    """
    if "version_source" in repo_info:
        component["properties"].append({
            "name": "version:source",
            "value": repo_info["version_source"]
        })


def is_git_repo(path: str) -> bool:
    """
    Check if the given path is a valid Git repository.
    
    Args:
        path: Path to check
        
    Returns:
        True if the path is a valid Git repository, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def get_repo_info(repo_path: str, root_path: str = None, version_config=None,
                  submodule_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about a Git repository.
    
    This function retrieves information about a Git repository, including its commit hash,
    branch, tags, and URL. If a version configuration is provided, it attempts to extract
    a version from files in the repository using the configuration.
    
    If version extraction fails, a warning is issued with a detailed error message explaining
    why the extraction failed. The error message will indicate whether:
    - No files matching the pattern were found
    - The regex pattern was invalid
    - The regex pattern didn't match the content of the files
    - There was an error reading the files
    
    This detailed error reporting helps diagnose issues with version extraction, making it
    clear whether the problem is with the file pattern or the regex pattern.
    
    Args:
        repo_path: Path to the Git repository
        root_path: Path to the root repository (used to determine if this is the main repository)
        version_config: Optional version configuration for extracting versions from files
        submodule_name: Optional submodule name from .gitmodules for diagnostics
        
    Returns:
        Dictionary containing repository information
    """
    # Get current commit hash
    hash_result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    commit_hash = hash_result.stdout.strip()
    
    # Get current branch
    branch_result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    branch = branch_result.stdout.strip()
    
    # Get all tags pointing to the current commit
    tags_result = subprocess.run(
        ["git", "-C", repo_path, "tag", "--points-at", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    tags = [tag for tag in tags_result.stdout.strip().split('\n') if tag]
    
    # Check if any tag points to the current commit
    has_tag = len(tags) > 0
    
    # Get remote URL
    url_result = subprocess.run(
        ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False
    )
    remote_url = url_result.stdout.strip() if url_result.returncode == 0 else ""
    
    # Clean the URL by removing any username
    clean_url = strip_username_from_url(remote_url)
    
    # Extract repository name from path
    repo_name = os.path.basename(os.path.abspath(repo_path))
    
    # Initialize result dictionary
    result = {
        "path": os.path.abspath(repo_path),
        "hash": commit_hash,
        "branch": branch,
        "tags": tags,
        "has_tag": has_tag,
        "url": clean_url,
        "submodules": [],
        "name": repo_name,
        "version_source": "hash"  # Default source is hash
    }
    
    # Try to extract version from files if configuration is provided
    extracted_version = None
    if version_config:
        try:
            # Determine if this is the main repository or a submodule
            # For submodules, we need to match the name pattern
            is_main_repo = False
            if root_path is not None:
                # If root_path is provided, check if this repo is the root repo
                # This allows the tool to correctly identify the main repository
                # even when it's specified as a command-line argument and is
                # different from the current working directory
                # Use realpath() to resolve symlinks and normalize paths
                is_main_repo = os.path.realpath(repo_path) == os.path.realpath(root_path)
            else:
                # Fallback to the old behavior for backward compatibility
                # This assumes the main repository is the current working directory
                # Use realpath() to resolve symlinks and normalize paths
                is_main_repo = os.path.realpath(repo_path) == os.path.realpath(os.getcwd())
            
            if is_main_repo:
                # Get main repository configuration
                config = version_config.get_main_config()
                if config:
                    extracted_version, error_message = version_config.extract_version(repo_path, config)
                    if extracted_version:
                        result["version"] = extracted_version
                        result["version_source"] = "file"
                    elif error_message:
                        # If configuration exists but no version can be extracted, issue a warning with the detailed error
                        # Check if this is a YAML-specific issue and provide more helpful message
                        if "YAML" in error_message or "yaml" in error_message:
                            warnings.warn(f"Could not extract version for main repository: {error_message}. This appears to be a YAML formatting issue. Please check your configuration file. Falling back to commit hash.")
                        else:
                            warnings.warn(f"Could not extract version for main repository using configuration: {error_message}. Falling back to commit hash.")
            else:
                # Get submodule configuration based on name
                config = version_config.get_submodule_config(repo_name)
                if config:
                    extracted_version, error_message = version_config.extract_version(repo_path, config)
                    if extracted_version:
                        result["version"] = extracted_version
                        result["version_source"] = "file"
                    elif error_message:
                        # If configuration exists but no version can be extracted, issue a warning with the detailed error
                        # Check if this is a YAML-specific issue and provide more helpful message
                        if "YAML" in error_message or "yaml" in error_message:
                            warnings.warn(f"Could not extract version for submodule '{repo_name}': {error_message}. This appears to be a YAML formatting issue. Please check your configuration file. Falling back to commit hash.")
                        else:
                            warnings.warn(f"Could not extract version for submodule '{repo_name}' using configuration: {error_message}. Falling back to commit hash.")
                elif submodule_name and submodule_name != repo_name:
                    alt_config = version_config.get_submodule_config(submodule_name)
                    if alt_config:
                        warnings.warn(
                            f"No version configuration matched folder name '{repo_name}' for submodule "
                            f"'{submodule_name}' (.gitmodules name). Matching is performed against the "
                            "folder name; please update name_pattern to match the folder name."
                        )
        except Exception as e:
            warnings.warn(f"Error extracting version: {e}")
    
    # If no version was extracted, use the commit hash
    if "version" not in result:
        result["version"] = commit_hash[:8]  # Use short commit hash as version
    
    return result


def get_submodules(repo_path: str) -> List[Dict[str, str]]:
    """
    Get a list of submodules in a Git repository.
    
    Args:
        repo_path: Path to the Git repository
        
    Returns:
        List of dictionaries containing submodule information
    """
    try:
        # Check if .gitmodules file exists
        gitmodules_path = os.path.join(repo_path, ".gitmodules")
        if not os.path.isfile(gitmodules_path):
            return []
        
        # Get submodule paths
        path_result = subprocess.run(
            ["git", "-C", repo_path, "config", "--file", ".gitmodules", "--get-regexp", "path"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if path_result.returncode != 0:
            return []
        
        submodules = []
        for line in path_result.stdout.strip().split('\n'):
            if not line:
                continue
            
            # Parse submodule path
            parts = line.split()
            if len(parts) < 2:
                continue
                
            submodule_name = parts[0].split('.')[1]
            submodule_path = parts[1]
            
            # Get submodule URL
            url_result = subprocess.run(
                ["git", "-C", repo_path, "config", "--file", ".gitmodules", 
                 f"submodule.{submodule_name}.url"],
                capture_output=True,
                text=True,
                check=False
            )
            
            remote_url = url_result.stdout.strip() if url_result.returncode == 0 else ""
            
            # Clean the URL by removing any username
            clean_url = strip_username_from_url(remote_url)
            
            submodules.append({
                "name": submodule_name,
                "path": submodule_path,
                "url": clean_url
            })
            
        return submodules
    except Exception as e:
        print(f"Error getting submodules: {e}", file=sys.stderr)
        return []


def analyze_repo_recursive(repo_path: str, root_path: str = None, version_config=None,
                           submodule_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a Git repository and its submodules recursively.
    
    Args:
        repo_path: Path to the Git repository
        root_path: Path to the root repository (used for calculating relative paths)
        version_config: Optional version configuration for extracting versions from files
        submodule_name: Optional submodule name from .gitmodules
        
    Returns:
        Dictionary containing repository information and submodule information
    """
    if not is_git_repo(repo_path):
        raise ValueError(f"Not a valid Git repository: {repo_path}")
    
    # If root_path is not provided, use repo_path as the root
    if root_path is None:
        root_path = repo_path
    
    # Get repository information
    repo_info = get_repo_info(repo_path, root_path, version_config, submodule_name=submodule_name)
    
    # If this is a submodule (not the root), convert path to relative
    if repo_path != root_path:
        # Calculate relative path from root
        abs_repo_path = os.path.abspath(repo_path)
        abs_root_path = os.path.abspath(root_path)
        
        # Make sure the path is relative to the root path
        if abs_repo_path.startswith(abs_root_path):
            rel_path = os.path.relpath(abs_repo_path, abs_root_path)
            repo_info["path"] = rel_path
    
    # Get submodules
    submodules = get_submodules(repo_path)
    
    # Analyze each submodule recursively
    for submodule in submodules:
        submodule_path = os.path.join(repo_path, submodule["path"])
        
        if not os.path.isdir(submodule_path):
            continue

        if is_git_repo(submodule_path):
            submodule_info = analyze_repo_recursive(
                submodule_path,
                root_path,
                version_config,
                submodule_name=submodule.get("name")
            )
            repo_info["submodules"].append(submodule_info)
    
    return repo_info


def convert_to_cyclonedx(repo_info: Dict[str, Any], component_type: Optional[str] = None, 
                   use_nested_components: bool = False) -> Dict[str, Any]:
    """
    Convert repository information to CycloneDX format.
    
    Args:
        repo_info: Repository information from analyze_repo_recursive
        component_type: Optional type to override the default component type
        use_nested_components: Whether to use nested components instead of dependencies structure
        
    Returns:
        Dictionary in CycloneDX format
    """
    # Create a basic CycloneDX document
    cyclonedx = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [
                {
                    "vendor": "Janosch Meyer",
                    "name": "sbom-git-sm",
                    "version": __version__
                }
            ]
        },
        "components": []
    }
    
    # If not using nested components, add dependencies section
    if not use_nested_components:
        cyclonedx["dependencies"] = []
    
    # Process the repository and its submodules
    if use_nested_components:
        # For nested components approach, we'll handle the structure differently
        process_repo_as_nested_component(repo_info, cyclonedx["components"], is_main_repo=True, component_type=component_type)
    else:
        # For bom-ref and dependencies approach (default)
        process_repo_as_component(repo_info, cyclonedx["components"], dependencies=cyclonedx["dependencies"], 
                                 is_main_repo=True, component_type=component_type)
    
    return cyclonedx


def process_repo_as_component(repo_info: Dict[str, Any], components: List[Dict[str, Any]], 
                       dependencies: Optional[List[Dict[str, Any]]] = None,
                       parent_ref: Optional[str] = None,
                       is_main_repo: bool = False, 
                       component_type: Optional[str] = None):
    """
    Process a repository as a CycloneDX component and add it to the components list.
    
    Args:
        repo_info: Repository information
        components: List of components to add to
        dependencies: List of dependencies to add to
        parent_ref: Reference to the parent component (if any)
        is_main_repo: Whether this is the main repository (True) or a submodule (False)
        component_type: Optional type to override the default type
    """
    # Extract repository name from path or URL
    repo_name = os.path.basename(repo_info["path"])
    if not repo_name and repo_info["url"]:
        repo_name = os.path.basename(repo_info["url"])
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
    
    # Create a unique bom-ref for this component
    bom_ref = f"pkg:git/{repo_name}@{repo_info['hash']}"
    
    # Determine component type
    if not is_main_repo:
        # Always use "library" for submodules
        comp_type = "library"
    elif component_type:
        # Use the provided component type if specified for main repo
        comp_type = component_type
    else:
        # Use "application" for the main repository by default
        comp_type = "application"
    
    # Create a component for this repository
    component = {
        "type": comp_type,
        "name": repo_name,
        "version": repo_info.get("version", repo_info["hash"][:8]),  # Use extracted version or short commit hash
        "purl": bom_ref,
        "bom-ref": bom_ref,  # Add bom-ref for dependencies
        "properties": [
            {
                "name": "git:branch",
                "value": repo_info["branch"]
            },
            {
                "name": "git:commit",
                "value": repo_info["hash"]
            },
            {
                "name": "git:commit.short",
                "value": repo_info["hash"][:8]
            },
            {
                "name": "git:path",
                "value": repo_info["path"]
            },
            {
                "name": "git:worktree.path",
                "value": repo_info["path"]
            }
        ]
    }
    
    # Add URL if available
    if repo_info["url"]:
        # Add as external reference
        component["externalReferences"] = [
            {
                "type": "vcs",
                "url": repo_info["url"]
            }
        ]
        
        # Also add as property
        component["properties"].append({
            "name": "git:remote.url",
            "value": repo_info["url"]
        })
    
    # Add tags if available
    if repo_info["tags"]:
        for tag in repo_info["tags"]:
            component["properties"].append({
                "name": "git:tag",
                "value": tag
            })
    
    # Add version source property if available
    add_version_source_property(component, repo_info)
    
    # Add component to the list
    components.append(component)
    
    # Add dependency relationship if this is a submodule and dependencies tracking is enabled
    if dependencies is not None and parent_ref is not None:
        # Check if parent already has a dependency entry
        parent_entry = next((d for d in dependencies if d["ref"] == parent_ref), None)
        
        if parent_entry:
            # Add this component as a dependency of the parent
            if "dependsOn" not in parent_entry:
                parent_entry["dependsOn"] = []
            parent_entry["dependsOn"].append(bom_ref)
        else:
            # Create a new dependency entry for the parent
            dependencies.append({
                "ref": parent_ref,
                "dependsOn": [bom_ref]
            })
    
    # Process submodules recursively
    for submodule in repo_info["submodules"]:
        # Don't pass component_type to submodules as they should always be "library" type
        process_repo_as_component(
            submodule, 
            components, 
            dependencies=dependencies,
            parent_ref=bom_ref,  # This component is the parent of its submodules
            is_main_repo=False
        )


def process_repo_as_nested_component(repo_info: Dict[str, Any], components: List[Dict[str, Any]], 
                              is_main_repo: bool = False, component_type: Optional[str] = None):
    """
    Process a repository as a CycloneDX component with nested subcomponents.
    
    Args:
        repo_info: Repository information
        components: List of components to add to
        is_main_repo: Whether this is the main repository (True) or a submodule (False)
        component_type: Optional type to override the default type
    """
    # Extract repository name from path or URL
    repo_name = os.path.basename(repo_info["path"])
    if not repo_name and repo_info["url"]:
        repo_name = os.path.basename(repo_info["url"])
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
    
    # Determine component type
    if not is_main_repo:
        # Always use "library" for submodules
        comp_type = "library"
    elif component_type:
        # Use the provided component type if specified for main repo
        comp_type = component_type
    else:
        # Use "application" for the main repository by default
        comp_type = "application"
    
    # Create a component for this repository
    # Create a unique bom-ref for this component
    bom_ref = f"pkg:git/{repo_name}@{repo_info['hash']}"
    
    component = {
        "type": comp_type,
        "name": repo_name,
        "version": repo_info.get("version", repo_info["hash"][:8]),  # Use extracted version or short commit hash
        "purl": bom_ref,
        "bom-ref": bom_ref,  # Add bom-ref for dependencies/nested structure
        "properties": [
            {
                "name": "git:branch",
                "value": repo_info["branch"]
            },
            {
                "name": "git:commit",
                "value": repo_info["hash"]
            },
            {
                "name": "git:commit.short",
                "value": repo_info["hash"][:8]
            },
            {
                "name": "git:path",
                "value": repo_info["path"]
            },
            {
                "name": "git:worktree.path",
                "value": repo_info["path"]
            }
        ]
    }
    
    # Add URL if available
    if repo_info["url"]:
        # Add as external reference
        component["externalReferences"] = [
            {
                "type": "vcs",
                "url": repo_info["url"]
            }
        ]
        
        # Also add as property
        component["properties"].append({
            "name": "git:remote.url",
            "value": repo_info["url"]
        })
    
    # Add tags if available
    if repo_info["tags"]:
        for tag in repo_info["tags"]:
            component["properties"].append({
                "name": "git:tag",
                "value": tag
            })
    
    # Add version source property if available
    add_version_source_property(component, repo_info)
    
    # Process submodules recursively and add them as nested components
    if repo_info["submodules"]:
        component["components"] = []
        for submodule in repo_info["submodules"]:
            # Don't pass component_type to submodules as they should always be "library" type
            process_repo_as_nested_component(submodule, component["components"], is_main_repo=False)
    
    # Add component to the list
    components.append(component)


def create_sbom(repo_path: Path, output_path: Optional[Path] = None, 
              component_type: Optional[str] = None, use_nested_components: bool = False,
              print_errors: bool = True, version_config=None) -> Dict[str, Any]:
    """
    Create a Software Bill of Materials (SBOM) from a git repository based on its submodules.
    
    Args:
        repo_path: Path to the git repository
        output_path: Optional path to save the SBOM to
        component_type: Optional type to override the default component type
        use_nested_components: Whether to use nested components instead of dependencies structure
        print_errors: Whether to print error messages to stderr (default: True)
        version_config: Optional version configuration for extracting versions from files
        
    Returns:
        A dictionary containing the SBOM data in CycloneDX format
    """
    try:
        # Convert Path to string
        repo_path_str = str(repo_path)
        
        # Analyze the repository
        if version_config is None:
            repo_info = analyze_repo_recursive(repo_path_str, repo_path_str)
        else:
            repo_info = analyze_repo_recursive(repo_path_str, repo_path_str, version_config)
        
        # Convert to CycloneDX format
        cyclonedx_sbom = convert_to_cyclonedx(repo_info, component_type, use_nested_components)
        
        # Write to file if output_path is provided
        if output_path:
            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cyclonedx_sbom, f, indent=2, ensure_ascii=False)
            print(f"SBOM written to {output_path}")
        
        return cyclonedx_sbom
    
    except Exception as e:
        if print_errors:
            print(f"Error creating SBOM: {e}", file=sys.stderr)
        # Return a minimal error SBOM
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tools": [
                    {
                        "vendor": "Janosch Meyer",
                        "name": "sbom-git-sm",
                        "version": __version__
                    }
                ],
                "component": {
                    "type": component_type if component_type else "application",
                    "name": "sbom-git-sm",
                    "version": __version__
                }
            },
            "components": [],
            "errors": [str(e)]
        }
