- [ ] Collect all target files/exts upfront so all possible paths can be collected by one get_files call
- [ ] Add support for having the build options in pyproject.toml
- [x] Make a new base class to suit more lightweight plugins like gperf, make them distinct from backends that need more true compilation like cython, c++, etc.
- [x] Fallback for gperf binary stuff
- [ ] Make it so users can add their own plugins
- [ ] Make it so users can add their own backends 
    - Basically we could make it easier to register plugins/backends with the system instead 
    of needing to cobble together stuff in different places. This will require a refactor of
    the config code however and might be more messy but would be more customizable and potentially
    less fragile.
    - Even internally we would do this to be consistent? 
    ```python
    registry.register_backend("cython", path_to_cython, backend_name, CythonSettingsModel)
    registry.register_plugin("gperf", ...)
    ```
    - Now that we have dynamic 

- [ ] On a similar note, potentially support plugins for templating, ie, provide a way to use user defined Pydantic Classes?
- [x] Research what we would need to do in order to not require UV Dynamic Versioning (the specific module) (IN PROGRESS)
- [x] Add pyo3 as a plugin
