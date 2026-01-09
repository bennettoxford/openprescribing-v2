import importlib
import pkgutil


def load_all_modules_with_method(path, name, method_name):
    helpers = {}
    for m in pkgutil.walk_packages(path=path):
        mod = importlib.import_module(name + "." + m.name)
        helpers[m.name] = getattr(mod, method_name)
    return helpers
