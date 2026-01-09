from openprescribing.data.utils.load_package_modules import (
    load_all_modules_with_function,
)


available_fetchers = load_all_modules_with_function(__path__, __name__, "fetch")
