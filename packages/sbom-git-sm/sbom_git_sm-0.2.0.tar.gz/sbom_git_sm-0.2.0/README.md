# sbom-git-sm

A tool to create a Software Bill of Materials (SBOM) from a git repository based on its submodules.

## Features

- Analyzes Git repositories and their submodules recursively
- Collects information about each repository:
  - Commit hash
  - Current branch
  - Tags pointing to the current commit
  - Remote URL of the repository
- Maintains the hierarchical structure of submodules in the output
- Outputs results in CycloneDX JSON format
- Command-line interface for easy integration into scripts and CI/CD pipelines
- Python API for programmatic usage
- Cross-platform compatibility (Windows and Linux)

## Installation

Make sure you have Python 3.7+ installed, then install the package:

```bash
pip install sbom-git-sm
```

## Usage

### Using the Command-line Interface

After installing the package:

```bash
sbom-git-sm [repo_path] [--output output_path] [--pretty]
```

### Using the Module Directly

If you haven't installed the package, you can run it as a module:

```bash
# Windows
python -m sbom_git_sm [repo_path] [--output output_path] [--pretty]

# Linux
python3 -m sbom_git_sm [repo_path] [--output output_path] [--pretty]
```

### Running the Script Directly

You can also run the cli.py script directly:

```bash
# Windows
python sbom_git_sm\cli.py [repo_path] [--output output_path] [--pretty]

# Linux
python3 sbom_git_sm/cli.py [repo_path] [--output output_path] [--pretty]
```

### Arguments

- `repo_path`: Path to the git repository (optional, defaults to current directory)
- `--output`, `-o`: Path to save the SBOM to (optional, if not provided, the SBOM will be printed to stdout)
- `--version`, `-v`: Show version information and exit
- `--pretty`, `-p`: Pretty-print the JSON output
- `--format`: Output format for the SBOM (currently only 'cyclonedx' is supported)
- `--spec-version`: CycloneDX specification version (currently only 1.4 is supported)
- `--component-type`: Override the default component type (default: "application" for main repo, "library" for submodules)
- `--nested-components`, `-n`: Use nested components instead of dependencies structure for representing hierarchical relationships
- `--version-config`, `-c`: Path to version configuration file (JSON or YAML) for custom version extraction

### Example

```bash
# Generate a CycloneDX SBOM for the current directory and save it to sbom.json
sbom-git-sm --output sbom.json --pretty

# Generate a CycloneDX SBOM for a specific repository
sbom-git-sm C:\path\to\git\repository --output repo_sbom.json --pretty

# Generate a CycloneDX SBOM with custom version extraction
sbom-git-sm --output sbom.json --version-config version_config.json --pretty
```

## Version Extraction

By default, the tool uses the short git commit hash (first 8 characters) as the version for each repository and submodule. However, you can customize how versions are extracted using a configuration file.

### Version Configuration File

The version configuration file allows you to specify regex patterns to extract versions from files in the repository and its submodules. The configuration file can be in either JSON or YAML format.

Example configuration files are available in the `examples` directory:
- [version_config.json](examples/version_config.json)
- [version_config.yaml](examples/version_config.yaml)

#### JSON Format Example

```json
{
  "main": {
    "file_pattern": "version.txt",
    "regex_pattern": "version\\s*=\\s*['\"]([^'\"]+)['\"]",
    "encoding": "utf-8"
  },
  "submodules": [
    {
      "name_pattern": "SubmoduleName",
      "file_pattern": "version.txt",
      "regex_pattern": "version\\s*=\\s*['\"]([^'\"]+)['\"]",
      "encoding": "utf-8"
    },
    {
      "name_pattern": ".*",
      "file_pattern": "*.txt",
      "regex_pattern": "([0-9]+\\.[0-9]+\\.[0-9]+)"
    }
  ]
}
```

#### YAML Format Example

```yaml
main:
  file_pattern: version.txt
  regex_pattern: version\s*=\s*['"]([^'"]+)['"]
  encoding: utf-8

submodules:
  - name_pattern: SubmoduleName
    file_pattern: version.txt
    regex_pattern: version\s*=\s*['"]([^'"]+)['"]
    encoding: utf-8
  - name_pattern: .*
    file_pattern: "*.txt"
    regex_pattern: ([0-9]+\.[0-9]+\.[0-9]+)
```

#### Special Characters in YAML Regex Patterns

When using YAML configuration files, you need to be careful with regex patterns that contain special characters, especially the `#` character. In YAML, the `#` character is used to denote comments, so any text after a `#` is ignored unless the text is properly quoted.

For example, if you want to match a C/C++ style define statement like `#define VERSION "1.0.0"`, you need to enclose the regex pattern in quotes:

**INCORRECT - This will not work because # starts a comment in YAML:**
```yaml
submodules:
  - name_pattern: TestSub1
    file_pattern: Version.h
    regex_pattern: #define\s+VERSION\s+"([0-9]+\.[0-9]+\.[0-9]+)"
    # ^ Everything after the # is treated as a comment!
```

**CORRECT - Enclose the pattern in quotes to include the # character:**
```yaml
submodules:
  - name_pattern: TestSub1
    file_pattern: Version.h
    regex_pattern: "#define\\s+VERSION\\s+\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
```

Other special characters that might need special handling in YAML include:
- Colons `:` (must be followed by a space when used as a key-value separator)
- Quotes `"` and `'` (need to be escaped or enclosed in the other type of quotes)
- Backslashes `\` (need to be doubled when inside double quotes)

When in doubt, always enclose your regex patterns in quotes in YAML files.

### Configuration Fields

- `main`: Configuration for the main repository
  - `file_pattern`: Glob pattern to match files to search for version information
  - `regex_pattern`: Regular expression to extract version from file content (first capture group is used)
  - `encoding`: Optional text encoding to use when reading files (default: utf-8, with BOM detection fallback)

- `submodules`: Array of configurations for submodules
  - `name_pattern`: Regular expression to match submodule names
  - `file_pattern`: Glob pattern to match files to search for version information
  - `regex_pattern`: Regular expression to extract version from file content (first capture group is used)
  - `encoding`: Optional text encoding to use when reading files (default: utf-8, with BOM detection fallback)

### Behavior

1. When a configuration is provided, the tool will attempt to extract versions using the specified patterns.
2. If a version cannot be extracted but a configuration exists, the tool will fall back to using the git commit hash and issue a warning.
3. If no configuration exists for a repository or submodule, the git commit hash will be used without a warning.
4. For submodules, the first matching configuration (based on `name_pattern`) will be used.
5. If multiple files match and contain a valid version, the tool uses the first match in deterministic path order and emits a warning listing all matches.

### Version Source Property

When using version extraction, a new property `version:source` is added to each component indicating whether the version was extracted from a file (`file`) or derived from the git commit hash (`hash`).

### YAML Support

YAML configuration files require the PyYAML package. You can install it in two ways:

1. Install the package with YAML support using the optional dependency:

```bash
pip install sbom-git-sm[yaml]
```

2. Or install PyYAML separately if you've already installed the package:

```bash
pip install PyYAML
```

## CycloneDX Output

The tool generates a CycloneDX Software Bill of Materials (SBOM) in JSON format. CycloneDX is a lightweight SBOM standard designed for use in application security contexts and supply chain component analysis.

Each Git repository and submodule is represented as a component in the CycloneDX document with the following information:

- Component type: main repository = "application", submodules = "library" (overridable for the main repo via `--component-type`)
- Component name: Derived from the repository path or URL
- Component version: Short commit hash
- Package URL (purl): Constructed from the repository name and full commit hash
- Properties:
  - git:branch: The current branch
  - git:commit: The full commit hash
  - git:commit.short: The short commit hash
  - git:path: The repository path (relative to the root repository for submodules)
  - git:worktree.path: The repository path (absolute in the main repo, relative for submodules)
  - git:tag: Any tags pointing to the current commit (if available)
- External references: The repository URL (if available)

### Hierarchical Relationship Representation

The tool supports two approaches for representing the hierarchical relationships between repositories and their submodules:

#### 1. Dependencies Structure (Default)

By default, the tool uses the CycloneDX dependencies structure to represent hierarchical relationships. This approach:

- Adds a unique `bom-ref` to each component
- Lists all components in a flat structure in the `components` array
- Uses a `dependencies` section to represent parent-child relationships
- Is fully compliant with the CycloneDX specification
- Makes the hierarchical relationships explicit and machine-readable

Example output with dependencies structure:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2025-12-06T17:30:45Z",
    "tools": [
      {
        "vendor": "Janosch Meyer",
        "name": "sbom-git-sm",
        "version": "0.1.0"
      }
    ]
  },
  "components": [
    {
      "type": "application",
      "name": "main-repo",
      "version": "abcdef12",
      "purl": "pkg:git/main-repo@abcdef1234567890",
      "bom-ref": "pkg:git/main-repo@abcdef1234567890",
      "properties": [
        {
          "name": "git:branch",
          "value": "main"
        },
        {
          "name": "git:commit",
          "value": "abcdef1234567890"
        },
        {
          "name": "git:commit.short",
          "value": "abcdef12"
        },
        {
          "name": "git:path",
          "value": "/path/to/main-repo"
        },
        {
          "name": "git:worktree.path",
          "value": "/path/to/main-repo"
        },
        {
          "name": "git:tag",
          "value": "v1.0.0"
        }
      ],
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/user/main-repo.git"
        }
      ]
    },
    {
      "type": "library",
      "name": "submodule1",
      "version": "12345678",
      "purl": "pkg:git/submodule1@1234567890abcdef",
      "bom-ref": "pkg:git/submodule1@1234567890abcdef",
      "properties": [
        {
          "name": "git:branch",
          "value": "main"
        },
        {
          "name": "git:commit",
          "value": "1234567890abcdef"
        },
        {
          "name": "git:path",
          "value": "submodule1"
        },
        {
          "name": "git:worktree.path",
          "value": "submodule1"
        }
      ],
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/user/submodule1.git"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:git/main-repo@abcdef1234567890",
      "dependsOn": [
        "pkg:git/submodule1@1234567890abcdef"
      ]
    }
  ]
}
```

#### 2. Nested Components (Alternative)

Alternatively, you can use the `--nested-components` flag to represent hierarchical relationships using nested components. This approach:

- Nests submodules within their parent components in a hierarchical structure
- Includes `bom-ref` fields for all components for validation compatibility
- Does not use the `dependencies` section
- May be more intuitive for visual inspection
- Represents the hierarchy directly in the component structure

Example output with nested components:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2025-12-06T17:30:45Z",
    "tools": [
      {
        "vendor": "Janosch Meyer",
        "name": "sbom-git-sm",
        "version": "0.1.0"
      }
    ]
  },
  "components": [
    {
      "type": "application",
      "name": "main-repo",
      "version": "abcdef12",
      "purl": "pkg:git/main-repo@abcdef1234567890",
      "bom-ref": "pkg:git/main-repo@abcdef1234567890",
      "properties": [
        {
          "name": "git:branch",
          "value": "main"
        },
        {
          "name": "git:commit",
          "value": "abcdef1234567890"
        },
        {
          "name": "git:commit.short",
          "value": "abcdef12"
        },
        {
          "name": "git:path",
          "value": "/path/to/main-repo"
        },
        {
          "name": "git:worktree.path",
          "value": "/path/to/main-repo"
        },
        {
          "name": "git:tag",
          "value": "v1.0.0"
        }
      ],
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/user/main-repo.git"
        }
      ],
      "components": [
        {
          "type": "library",
          "name": "submodule1",
          "version": "12345678",
          "purl": "pkg:git/submodule1@1234567890abcdef",
          "bom-ref": "pkg:git/submodule1@1234567890abcdef",
          "properties": [
            {
              "name": "git:branch",
              "value": "main"
            },
            {
          "name": "git:commit",
          "value": "1234567890abcdef"
        },
        {
          "name": "git:commit.short",
          "value": "12345678"
        },
        {
          "name": "git:path",
          "value": "submodule1"
        },
        {
          "name": "git:worktree.path",
          "value": "submodule1"
        }
      ],
      "externalReferences": [
        {
          "type": "vcs",
              "url": "https://github.com/user/submodule1.git"
            }
          ]
        }
      ]
    }
  ]
}
```

## Development

### Package Build Artifacts

When building the Python package, several files and directories are created that should not be tracked in version control:

- **Distribution files**: `dist/` directory containing wheel and source distribution files
- **Build files**: `build/` directory used during the build process
- **Metadata files**: `*.egg-info/` directories containing package metadata
- **Python cache files**: `__pycache__/` directories and `.pyc` files
- **Virtual environments**: `venv/`, `env/`, etc.

These files are automatically excluded from git by the `.gitignore` file.

### Building the Package

To build the package, run:

```bash
python -m pip install build
python -m build
```

This will create both wheel and source distributions in the `dist/` directory.

## Trademarks

Git and the Git logo are either registered trademarks or trademarks of Software Freedom Conservancy, Inc., corporate home of the Git Project, in the United States and/or other countries. This project is not affiliated with or endorsed by them.

## License

This project is open source and available under the MIT License.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This project was created with the assistance of artificial intelligence.
