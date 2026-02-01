<!-- toc:insertAfterHeading=pyvscodeextroh -->
<!-- toc:insertAfterHeadingOffset=4 -->


# pyvscodeextroh

_The pyvscodeextroh package can be used to manage VSCode extensions via policy file, 
remotely or via MDM solution._

## Table of Contents

1. [Introduction](#introduction)
1. [Getting started](#getting-started)
    1. [Prerequisites](#prerequisites)
    1. [Installation](#installation)
1. [How to use](#how-to-use)
    1. [How to import](#how-to-import)
    1. [Using the module](#using-the-module)
1. [Releasing](#releasing)
1. [License](#license)

## Introduction

While software, driver, hardware and everything else is managed by organizations, most of them, are not managing their dev environments at all.

With emerging threads in dev environments and software supply chain, managing dev environments is and will be crucial for organizations in the future.

This python package aims to centralize the extension management on linux dev environments for VSCode via remote connections or MDM solutions like Ansible.

You can find an overview of all policies [here][VSCodePolicies].

## Getting started

### Prerequisites

- Python installed
- Operatingsystem: Linux or Windows, not tested on mac
- IDE like VS Code, if you want to contribute or change the code

### Installation

There are two ways to install this module depending on the way you work and the preinstalled modules:

1. ```pip install pyvscodeextroh```
2. ```python -m pip install pyvscodeextroh```

## How to use

### How to import

You can import the module in two ways:

```python
import pyvscodeextroh
```

This will import all functions. Even the ones that are not supposed to be used (helper functions).

```python
from pyvscodeextroh import *
```

This will import only the significant functions, meant for using.

### Using the module

You can do the following things:

- Add/Remove extensions to policy file
- Add/Remove publishers to policy file
- Deny extensions/publishers via policy file
- Install/Uninstall specific extensions
- Enforce the current policy file

Every command requires ***sudo*** priviliges.

The following examples show how to use this package and its modules in a script.

Example 1: Add a publisher to the policy

With this code only extensions from MS can be installed on the current machine.

```python
# Add a publisher
from pyvscodeextroh.policy_editor import PolicyEditor
# Create an editor
editor = PolicyEditor()
# Allow all extensions from the publisher "microsoft"
editor.allow_publisher("microsoft")

# Result:
# Creates the file /etc/vscode/policy.json if it does not exist
# Appends follwing lines
# "AllowedExtensions": {
#    "microsoft": true
# }
```

Example 2: Enforce VSCode policy

This will enforce a policy from the */etc/vscode/policy.json*. It force uninstalls all unallowed extensions.

```python
from pyvscodeextroh import VSCodePolicyManager
# Use the default system policy file (/etc/vscode/policy.json)
pm = VSCodePolicyManager()
# Uninstall all unallowed extensions
pm.enforce_policy()
```

You can also use a custom policy file, if you want extensions managed seperated from other configurations like MCP, AI, ... .

A custom policy file has to look like:

```json
{
    "AllowedExtensions": {
        "microsoft": true,
        "github": true,
        "ms-python.python": true,
        "evilcorp": false,
        "evilcorp.malware": false
    }
}
```

## Releasing

Releases are published automatically when a tag is pushed to GitHub.

```Powershell
# Create release variable.
$Release = "x.x.x"
# Create commit.
git commit --allow-empty -m "Release $Release"
# Create tag.
git tag -a $Release -m "Version $Release"
# Push from original.
git push origin --tags
# Push from fork.
git push upstream --tags
```

## License

[MIT][License]

[VSCodePolicies]: https://code.visualstudio.com/docs/enterprise/policies
[License]: ./LICENSE