#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : Recommender Systems: Towards Deep Learning State-of-the-Art                         #
# Version    : 0.1.0                                                                               #
# Python     : 3.10.6                                                                              #
# Filename   : /recsys/core/dal/sql/base.py                                                        #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john.james.ai.studio@gmail.com                                                      #
# URL        : https://github.com/john-james-ai/Recommender-Systems                                #
# ------------------------------------------------------------------------------------------------ #
# Created    : Friday December 16th 2022 02:57:58 am                                               #
# Modified   : Saturday January 7th 2023 11:37:54 am                                               #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2022 John James                                                                 #
# ================================================================================================ #
from dataclasses import dataclass
from abc import ABC
# ------------------------------------------------------------------------------------------------ #

# ------------------------------------------------------------------------------------------------ #
#                                  SQL COMMAND ABC                                                 #
# ------------------------------------------------------------------------------------------------ #


@dataclass
class SQL(ABC):  # pragma: no cover
    """Base class for SQL Command Objects."""


# ------------------------------------------------------------------------------------------------ #
#                             DDL AGGREGATION BASE CLASS                                           #
# ------------------------------------------------------------------------------------------------ #
@dataclass
class DDL(ABC):  # pragma: no cover
    """Base class for entity Data Definition Language (DDL)."""

    create: SQL
    drop: SQL
    exists: SQL


# ------------------------------------------------------------------------------------------------ #
#                             DML AGGREGATION BASE CLASS                                           #
# ------------------------------------------------------------------------------------------------ #
@dataclass
class DML(ABC):  # pragma: no cover
    """Base class for entity Data Manipulation Language (DML)."""
    insert: type(SQL) = None
    update: type(SQL) = None
    select: type(SQL) = None
    select_all: type(SQL) = None
    exists: type(SQL) = None
    delete: type(SQL) = None


# ------------------------------------------------------------------------------------------------ #
#                    OBJECT QUERY & MANIPULATION LANGUAGE BASE CLASSES                             #
# ------------------------------------------------------------------------------------------------ #
@dataclass
class OCL(ABC):
    """Object Oriented Command Language"""


@dataclass
class ODL(ABC):
    """Commands that define and manage the object store"""


@dataclass
class OQL(OCL):  # pragma: no cover
    """Commands that query data."""


@dataclass
class OML(OCL):  # pragma: no cover
    """Commands that manipulate data."""
