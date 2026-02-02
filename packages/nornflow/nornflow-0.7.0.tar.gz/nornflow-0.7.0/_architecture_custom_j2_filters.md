### Conventional Commit Branch Name
```
feat/custom-jinja2-filters
```

### Architectural Document: Adding Support for User-Defined Custom Jinja2 Filters in NornFlow

#### Overview
This feature introduces support for user-defined custom Jinja2 filters in NornFlow, allowing users to extend the templating system with their own filter functions. The core implementation will reside in the `nornflow.j2/*` package, maintaining consistency with NornFlow's modular architecture. Users will be able to define custom filters in Python modules, configure them via a new NornFlow setting, and have them automatically registered in the Jinja2 environment alongside built-in filters.

Key goals:
- **User Extensibility**: Enable users to add custom filters without modifying NornFlow's core code.
- **Global Registration**: Register filters directly (like hooks) for seamless availability in all Jinja2 contexts.
- **Seamless Integration**: Custom filters must be automatically available in all Jinja2 contexts (workflows, blueprints, hooks).
- **CLI Support**: Provide commands to initialize directories and display registered filters.
- **Backward Compatibility**: Ensure existing functionality remains unchanged.

#### High-Level Architecture
- **Filter Sources**:
  - **Built-in Filters**: Static registry in `nornflow.builtins.jinja2_filters` (renamed from `ALL_FILTERS` to `ALL_BUILTIN_J2_FILTERS` for clarity).
  - **Custom Filters**: Dynamic loading from user-specified directories, registered directly without a catalog.
- **Registration**: `Jinja2Service` will register both built-in and custom filters into the Jinja2 environment. Custom filters are loaded via `import_modules_recursively` (similar to hooks) and registered globally.
- **Configuration**: A new NornFlow setting (`local_j2_filters`) will specify directories for custom filter modules.
- **Discovery**: Custom filters will be loaded recursively from configured directories and registered immediately.
- **CLI Integration**: `nornflow init` will create a default directory; `nornflow show --j2-filters` will display registered filters by querying the Jinja2 environment.

#### Roadmap to Implementation
This roadmap outlines the step-by-step implementation, focusing on incremental changes to minimize disruption. Each step includes prerequisites, deliverables, and integration points.

1. **Rename Built-in Filters Registry (Preparation Step)**:
   - **Objective**: Clarify the distinction between built-in and custom filters.
   - **Changes**: In `nornflow.builtins.jinja2_filters.__init__.py`, rename `ALL_FILTERS` to `ALL_BUILTIN_J2_FILTERS`. Update all references in the codebase (e.g., in `Jinja2Service`).
   - **Deliverables**: Updated module with clear naming.
   - **Integration**: Ensures no conflicts with new custom filter registry.

2. **Add New NornFlow Setting for Custom Filters**:
   - **Objective**: Allow users to configure directories for custom filter modules.
   - **Changes**: Add `local_j2_filters: list[str]` to `NornFlowSettings` (default: `["jinja2_filters"]`). Update environment variable support and validation.
   - **Deliverables**: Modified settings.py with the new setting.
   - **Integration**: Setting will be used by direct loading logic.

3. **Update Sample NornFlow Configuration**:
   - **Objective**: Provide a default example for the new setting.
   - **Changes**: Add `local_j2_filters: ["jinja2_filters"]` to nornflow.yaml.
   - **Deliverables**: Updated sample config file.
   - **Integration**: Ensures users see the setting during `nornflow init`.

4. **Modify CLI Init to Create Custom Filters Directory**:
   - **Objective**: Automatically create a default directory for custom filters during project initialization.
   - **Changes**: Update `nornflow.cli.init` to create a `jinja2_filters` directory (based on the new setting's default). Add a sample placeholder file (e.g., __init__.py or a README).
   - **Deliverables**: Enhanced init logic and sample directory structure.
   - **Integration**: Aligns with existing directory creation for tasks/workflows.

5. **Add CLI Show Option for Registered Jinja2 Filters**:
   - **Objective**: Allow users to view all registered Jinja2 filters (built-in + custom).
   - **Changes**: Add `--j2-filters` option to `nornflow.cli.show`. Implement display logic to list filters by querying the Jinja2 environment (no catalog needed). Show descriptions and sources (built-in vs. custom).
   - **Deliverables**: Updated show command with new option and table rendering.
   - **Integration**: Reuses existing display patterns; distinguishes from `--filters` (Nornir inventory filters).

6. **Implement Direct Registration for Custom Filters**:
   - **Objective**: Load and register custom filters directly without a catalog, using existing module discovery patterns.
   - **Changes**: Create a utility function (e.g., in a new module like `_architecture_custom_j2_filters.py`) that uses `import_modules_recursively` to load modules from `local_j2_filters` directories and registers filters in the Jinja2 environment. No `CallableCatalog` or dynamic lookup—filters are available globally once registered.
   - **Deliverables**: Utility module for direct registration.
   - **Integration**: Similar to hook registration; ensures filters are loaded early and available in all contexts.

7. **Update Jinja2Service to Register Custom Filters**:
   - **Objective**: Ensure custom filters are available in the Jinja2 environment from the start.
   - **Changes**: Modify `Jinja2Service` to accept and register custom filters alongside built-ins during initialization. Call the direct registration utility early.
   - **Deliverables**: Enhanced `Jinja2Service` with integrated custom filter registration.
   - **Integration**: Filters are registered once per service instance; available in all resolution contexts, including assembly-time (e.g., for blueprints).

8. **Integrate Custom Filters Loading in NornFlow Core**:
   - **Objective**: Wire the direct registration into NornFlow's initialization for early loading.
   - **Changes**: Update `NornFlow.__init__` to call the direct registration utility after settings are loaded but before workflow creation/assembly. Ensure registration happens in the builder or core init.
   - **Deliverables**: Modified core initialization logic with early filter loading.
   - **Integration**: Ensures custom filters are loaded early and available globally, including for blueprint expansion.

9. **Testing and Validation**:
   - **Objective**: Verify end-to-end functionality.
   - **Changes**: Add unit tests for direct loading, filter registration, and CLI commands. Test custom filters in workflows/blueprints.
   - **Deliverables**: Comprehensive test suite.
   - **Integration**: Validates the feature works across all use cases.

#### Potential Challenges and Mitigations
- **Naming Conflicts**: Between built-in and custom filters. Mitigate by prioritizing custom filters or raising errors on conflicts.
- **Performance**: Loading many custom modules. Mitigate with lazy loading and caching.
- **Security**: Custom code execution. Mitigate with warnings and user responsibility (similar to custom tasks).
- **Backward Compatibility**: Ensure no breaking changes. Mitigate by keeping built-ins unchanged.

#### Dependencies and Prerequisites
- Relies on existing module discovery patterns in NornFlow (e.g., `import_modules_recursively` for hooks).
- Assumes users follow Python module conventions for custom filters (e.g., functions with specific signatures).
- No external dependencies beyond existing Jinja2 integration.

This roadmap provides a structured path to implement the feature incrementally. Once approved, we can proceed step-by-step with code implementation.



-----------


After analyzing the diffs and the full codebase, here are the required documentation changes:

## 1. nornflow_settings.md - Add new `local_j2_filters` setting

Add a new section after `local_blueprints`:

```markdown
### `local_j2_filters`

- **Description**: List of paths to directories containing custom Jinja2 filter functions. These filters extend the built-in Jinja2 filters available in NornFlow templates. The search is recursive, meaning all subdirectories will be searched. Both absolute and relative paths are supported.
- **Type**: list[str]
- **Default**: ["j2_filters"]
- **Path Resolution**: 
  - When loaded through `NornFlowSettings.load`, relative paths resolve against the settings file directory
  - Absolute paths are used as-is
- **Example**:
  ```yaml
  local_j2_filters:
    - "j2_filters"
    - "/opt/company/shared_filters"
  ```
- **Environment Variable**: `NORNFLOW_SETTINGS_LOCAL_J2_FILTERS`
- **Note**: Custom filters defined in these directories will be registered with the Jinja2 environment and can be used in any template throughout NornFlow (workflows, blueprints, task arguments, etc.). See the [Jinja2 Filters Reference](jinja2_filters.md) for details on creating custom filters.
```

## 2. quick_start.md - Update project structure and commands

Update the directory structure created by `nornflow init`:

```markdown
This creates:
- 📁 tasks - Where your Nornir tasks should live
- 📁 workflows - Holds YAML workflow definitions
- 📁 filters - Custom Nornir inventory filters
- 📁 hooks - Custom hook implementations for extending task behavior
- 📁 blueprints - Reusable task collections
- 📁 j2_filters - Custom Jinja2 filters for templates
- 📁 vars - Will contain Global and Domain-specific default variables
- 📁 nornir_configs - Nornir configuration
- 📑 nornflow.yaml - NornFlow settings
```

Update the "Useful Commands" section to include:

```markdown
# Show specific catalogs
nornflow show --tasks
nornflow show --filters
nornflow show --workflows
nornflow show --blueprints
nornflow show --j2-filters
```

## 3. jinja2_filters.md - Add section on custom filters

Add a new section after "Common Patterns" or as its own major section:

```markdown
## Custom Jinja2 Filters

NornFlow allows you to define custom Jinja2 filters that can be used throughout your workflows, blueprints, and task arguments.

### Creating Custom Filters

Custom filters are Python functions placed in directories specified by `local_j2_filters` in your `nornflow.yaml`:

```yaml
# nornflow.yaml
local_j2_filters:
  - "j2_filters"
```

Each filter is a simple Python function that takes at least one argument (the value being filtered) and returns the transformed value:

```python
# j2_filters/my_filters.py

def join_data(items: list) -> str:
    """Joins list elements with '***' separator.
    
    Args:
        items: List of items to join.
    
    Returns:
        Joined string with '***' between elements.
    """
    return '***'.join(str(item) for item in items)


def add_prefix(value: str, prefix: str = "NF_") -> str:
    """Add a prefix to a string value.
    
    Args:
        value: The string to prefix.
        prefix: The prefix to add (default: "NF_").
    
    Returns:
        Prefixed string.
    """
    return f"{prefix}{value}"
```

### Using Custom Filters

Once defined, custom filters are automatically discovered and can be used in any Jinja2 template:

```yaml
workflow:
  name: "Custom Filter Demo"
  tasks:
    - name: echo
      args:
        msg: "{{ [1, 2, 3] | join_data }}"  # Output: "1***2***3"
    
    - name: echo
      args:
        msg: "{{ hostname | add_prefix('DEVICE_') }}"
```

### Viewing Available Filters

To see all available Jinja2 filters (both built-in and custom):

```bash
nornflow show --j2-filters
```

This displays a table with filter names, descriptions (from docstrings), and their source location.

### Filter Discovery Rules

- All `.py` files in configured directories are scanned recursively
- All callable functions are registered as filters
- Filter names match the function names
- Docstrings are used for descriptions in the catalog display
- Custom filters override built-in filters with the same name
```

## 4. `docs/core_concepts.md` - Update catalogs section

If there's a section about catalogs, add J2 Filters Catalog:

```markdown
### J2 Filters Catalog

The J2 Filters Catalog contains all available Jinja2 filters:
- **Built-in filters**: NornFlow's custom filters and Python wrapper filters
- **Custom filters**: User-defined filters from `local_j2_filters` directories

View with: `nornflow show --j2-filters`
```

## 5. api_reference.md - Add j2_filters_catalog property

In the NornFlow Class Properties table, add:

```markdown
| `j2_filters_catalog` | `CallableCatalog` | Registry of Jinja2 filters |
```

## Summary of Changes

| File | Change Type | Description |
|------|-------------|-------------|
| nornflow_settings.md | Addition | Add `local_j2_filters` setting documentation |
| quick_start.md | Update | Add j2_filters directory to init output, add `--j2-filters` to show commands |
| jinja2_filters.md | Addition | Add "Custom Jinja2 Filters" section explaining how to create and use custom filters |
| core_concepts.md | Update | Add J2 Filters Catalog to catalogs section (if exists) |
| api_reference.md | Update | Add `j2_filters_catalog` property to NornFlow class |