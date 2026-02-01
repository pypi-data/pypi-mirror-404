# ruff: noqa: A001

import builtins
from decimal import Decimal
from pathlib import Path

from environs import env

from ._field_method import FieldMethod, ListFieldMethod

str: FieldMethod[builtins.str] = FieldMethod(env.str)
bool: FieldMethod[builtins.bool] = FieldMethod(env.bool)
int: FieldMethod[builtins.int] = FieldMethod(env.int)
float: FieldMethod[builtins.float] = FieldMethod(env.float)
decimal: FieldMethod[Decimal] = FieldMethod(env.decimal)
list: ListFieldMethod = ListFieldMethod(env.list)
path: FieldMethod[Path] = FieldMethod(env.path)
