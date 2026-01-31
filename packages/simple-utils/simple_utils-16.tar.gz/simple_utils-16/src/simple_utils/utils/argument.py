"""Argument module."""
import argparse
from typing import Any, Dict, Optional, Union

from simple_utils.utils.notebook import is_notebook
from simple_utils.utils.structure import dotdict


def parse_arguments(
    param: Optional[Dict[str, Any]] = None,
    description: str = "",
) -> Union[argparse.Namespace, dotdict]:
    """Parse arguments."""
    param = param if param is not None else {}
    namespace = dotdict()

    for name, user_args in param.items():
        if not isinstance(user_args, dict):
            param[name] = {
                "default": user_args,
            }

    if not is_notebook():
        parser = argparse.ArgumentParser(description=description)

        for name, user_args in param.items():
            action = user_args.get("action", "")

            if "store_" in action:
                user_args["required"] = False
                user_args.pop("default", None)
            else:
                user_args["required"] = user_args.get("required", True)

            parser.add_argument(f"--{name}", **user_args)

        namespace = parser.parse_args()

    else:
        for name, user_args in param.items():
            namespace[name] = user_args["default"]

        namespace = dotdict(namespace)

    return namespace
