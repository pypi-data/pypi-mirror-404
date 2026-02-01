User Guide
==========

Comprehensive documentation for all Vidhi features.

.. toctree::
   :maxdepth: 2

   frozen_dataclasses
   cli
   polymorphic
   yaml
   ide
   shell_completion
   api


Best Practices
--------------

1. **Use enums for type discriminators** - Provides type safety and IDE support
2. **Provide sensible defaults** - Make configurations easy to use out of the box
3. **Document with help text** - Use ``field(help="...")`` for CLI documentation
4. **Group related configs** - Use nested dataclasses for organization
5. **Validate in __post_init__** - Check constraints during initialization
6. **Keep configs immutable** - Don't work around the frozen constraint
7. **Generate JSON Schema** - Enable IDE autocomplete for config files
