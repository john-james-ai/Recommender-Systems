#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : Recommender Systems: Towards Deep Learning State-of-the-Art                         #
# Version    : 0.1.0                                                                               #
# Python     : 3.10.6                                                                              #
# Filename   : /recsys/core/dal/dao.py                                                             #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john.james.ai.studio@gmail.com                                                      #
# URL        : https://github.com/john-james-ai/Recommender-Systems                                #
# ------------------------------------------------------------------------------------------------ #
# Created    : Sunday December 4th 2022 06:27:36 am                                                #
# Modified   : Sunday January 1st 2023 06:44:37 am                                                 #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2022 John James                                                                 #
# ================================================================================================ #
"""Data Layer Services associated with Database construction."""
from abc import ABC, abstractmethod
import pandas as pd
from collections import OrderedDict
from typing import Dict, Tuple, List
import logging

from recsys.core.database.relational import RDB
from recsys.core.database.object import ODB
from .dto import DTO, DataFrameDTO, DatasetDTO, ProfileDTO, TaskDTO, JobDTO, FileDTO, DataSourceDTO, DataSourceURLDTO
from .base import DML
from recsys.core.entity.base import Entity


# ------------------------------------------------------------------------------------------------ #
#                                    BASE DATA ACCESS OBJECT                                       #
# ------------------------------------------------------------------------------------------------ #


class DAO(ABC):
    """Data Access Object

    Provides access to the underlying database and object storage for entities and aggregates.

    Args:
        rdb (RDB): Relational database object.
        odb (ODB): The object database storage.
        dml (DML): The Data Manipulation Language SQL objects.
    """

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        self._rdb = rdb
        self._odb = odb
        self._dml = dml
        self._entity = self.__class__.__name__.replace("DAO", "")
        self._logger = logging.getLogger(
            f"{self.__module__}.{self.__class__.__name__}",
        )

    def __len__(self) -> int:
        result = self.read_all()
        length = 0 if result is None else len(result)
        return length

    def begin(self) -> None:
        """Begins a transaction."""
        cmd = self._dml.begin()
        self._rdb.begin(cmd.sql, cmd.args)

    def create(self, entity: Entity, persist: bool = True) -> Entity:
        """Adds an entity to the database.

        Args:
            entity (Entity): Entity
            persist (bool): Indicates whether the entity was persisted in the
                object database

        Returns: entity with id set.
        """
        dto = entity.as_dto()
        cmd = self._dml.insert(dto)
        entity.id = self._rdb.insert(cmd.sql, cmd.args)
        if persist:
            self._odb.create(entity)
        return entity

    def read(self, id: int) -> Entity:
        """Retrieves an entity from the database, based upon id
        Args:
            id (int): The id for the entity.

        Returns a Entity
        """
        cmd = self._dml.select(id)
        row = self._rdb.select(cmd.sql, cmd.args)
        if len(row) > 0:
            dto = self._row_to_dto(row[0])
            return self._odb.read(dto.oid)
        else:
            msg = f"{self._entity}.{id} does not exist."
            self._logger.info(msg)
            raise FileNotFoundError(msg)

    def read_by_name_mode(self, name: str, mode: str) -> DTO:
        """Retrieves an entity from the database, based upon name
        Args:
            name (str): The name assigned to the entity.

        Returns a Data Transfer Object (DTO)
        """
        cmd = self._dml.select_by_name_mode(name, mode)

        row = self._rdb.select(cmd.sql, cmd.args)
        if len(row) > 0:
            dto = self._row_to_dto(row[0])
            return self._odb.read(dto.oid)
        else:
            msg = f"{self._entity}.{name} does not exist."
            self._logger.info(msg)
            raise FileNotFoundError(msg)

    def read_all(self) -> Dict[int, Entity]:
        """Returns a dictionary of Entities."""
        entities = {}
        cmd = self._dml.select_all()
        rows = self._rdb.select(cmd.sql, cmd.args)
        if len(rows) > 0:
            for row in rows:
                dto = self._row_to_dto(row)
                entities[dto.id] = self._odb.read(dto.oid)
        else:
            msg = "There are no Entities in the database."
            self._logger.info(msg)
        return entities

    def read_by_parent_id(self, parent: Entity) -> pd.DataFrame:
        """Returns all table data in a pandas DataFrame."""
        metadata = pd.DataFrame()
        cmd = self._dml.select_by_parent_id(parent.id)
        rows = self._rdb.select(cmd.sql, cmd.args)
        if len(rows) > 0:
            for row in rows:
                dto = self._row_to_dto(row)
                df = pd.DataFrame(data=dto.as_dict(), index=[0])
                metadata = pd.concat([metadata, df], axis=0)
        return metadata

    def update(self, entity: Entity, persist: bool = True) -> None:
        """Updates an existing entity.

        Args:
            dto (DTO): Data Transfer Object
            persist (bool): Indicates whether the entity was persisted in the
                object database
        """
        dto = entity.as_dto()
        cmd = self._dml.update(dto)
        self._rdb.update(cmd.sql, cmd.args)
        if persist:
            self._odb.update(entity)

    def exists(self, id: int) -> bool:
        """Returns True if the entity with id exists in the database.

        Args:
            id (int): id for the entity
        """
        cmd = self._dml.exists(id)
        return self._rdb.exists(cmd.sql, cmd.args)

    def delete(self, id: int, persist=True) -> None:
        """Deletes a Entity from the registry, given an id.
        Args:
            id (int): The id for the entity to delete.
            persist (bool): Indicates whether the entity was persisted in the
                object database
        """
        if persist:
            entity = self.read(id)
            try:
                self._odb.delete(entity.oid)
            except KeyError:
                msg = f"Unable to delete object id {entity.id} as it does not exist."
                self._logger.info(msg)
                raise RuntimeWarning(msg)

        cmd = self._dml.delete(id)
        self._rdb.delete(cmd.sql, cmd.args)

    def save(self) -> None:
        """Commits the changes to the database."""
        self._rdb.save()
        self._odb.save()

    def _rows_to_dict(self, results: List) -> Dict:
        """Converts the results to a dictionary of DTO objects."""
        results_dict = OrderedDict()
        for row in results:
            dto = self._row_to_dto(row)
            results_dict[dto.id] = dto
        return results_dict

    @abstractmethod
    def _row_to_dto(self, row: Tuple) -> DTO:
        """Converts a row from the Database into a Data Transfer Object."""


# ------------------------------------------------------------------------------------------------ #
#                                 DATAFRAME DATA ACCESS OBJECT                                     #
# ------------------------------------------------------------------------------------------------ #
class DataFrameDAO(DAO):
    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> DataFrameDTO:
        try:
            return DataFrameDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                datasource=row[4],
                mode=row[5],
                stage=row[6],
                size=row[7],
                nrows=row[8],
                ncols=row[9],
                nulls=row[10],
                pct_nulls=row[11],
                dataset_id=row[12],
                created=row[13],
                modified=row[14],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                 DATASET DATA ACCESS OBJECT                                       #
# ------------------------------------------------------------------------------------------------ #
class DatasetDAO(DAO):
    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> DataFrameDTO:
        try:
            return DatasetDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                datasource=row[4],
                mode=row[5],
                stage=row[6],
                task_id=row[7],
                created=row[8],
                modified=row[9],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                 PROFILE DATA ACCESS OBJECT                                       #
# ------------------------------------------------------------------------------------------------ #
class ProfileDAO(DAO):
    """Profile for Tasks"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> ProfileDTO:
        try:
            return ProfileDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                start=row[4],
                end=row[5],
                duration=row[6],
                user_cpu_time=row[7],
                percent_cpu_used=row[8],
                total_physical_memory=row[9],
                physical_memory_available=row[10],
                physical_memory_used=row[11],
                percent_physical_memory_used=row[12],
                active_memory_used=row[13],
                disk_usage=row[14],
                percent_disk_usage=row[15],
                read_count=row[16],
                write_count=row[17],
                read_bytes=row[18],
                write_bytes=row[19],
                read_time=row[20],
                write_time=row[21],
                bytes_sent=row[22],
                bytes_recv=row[23],
                task_id=row[24],
                created=row[25],
                modified=row[26],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                TASK DATA ACCESS OBJECT                                           #
# ------------------------------------------------------------------------------------------------ #
class TaskDAO(DAO):
    """Task Data Access Object"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> TaskDTO:
        try:
            return TaskDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                mode=row[4],
                state=row[5],
                job_id=row[6],
                created=row[7],
                modified=row[8],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                 JOB DATA ACCESS OBJECT                                           #
# ------------------------------------------------------------------------------------------------ #
class JobDAO(DAO):
    """Job Data Access Object"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> JobDTO:
        try:
            return JobDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                mode=row[4],
                state=row[5],
                created=row[6],
                modified=row[7],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                 FILE DATA ACCESS OBJECT                                          #
# ------------------------------------------------------------------------------------------------ #
class FileDAO(DAO):
    """File Data Access Object"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> FileDTO:
        try:
            return FileDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                datasource=row[4],
                mode=row[5],
                stage=row[6],
                uri=row[7],
                size=row[8],
                task_id=row[9],
                created=row[10],
                modified=row[11],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                                 DATA SOURCE ACCESS OBJECT                                        #
# ------------------------------------------------------------------------------------------------ #
class DataSourceDAO(DAO):
    """File Data Access Object"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> FileDTO:
        try:
            return DataSourceDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                website=row[4],
                mode=row[5],
                created=row[6],
                modified=row[7],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)


# ------------------------------------------------------------------------------------------------ #
#                               DATA SOURCE URL ACCESS OBJECT                                      #
# ------------------------------------------------------------------------------------------------ #
class DataSourceURLDAO(DAO):
    """File Data Access Object"""

    def __init__(self, rdb: RDB, odb: ODB, dml: DML) -> None:
        super().__init__(rdb=rdb, odb=odb, dml=dml)

    def _row_to_dto(self, row: Tuple) -> FileDTO:
        try:
            return DataSourceURLDTO(
                id=row[0],
                oid=row[1],
                name=row[2],
                description=row[3],
                url=row[4],
                mode=row[5],
                datasource_id=row[6],
                created=row[7],
                modified=row[8],
            )

        except IndexError as e:  # pragma: no cover
            msg = f"Index error in_row_to_dto method.\n{e}"
            self._logger.error(msg)
            raise IndexError(msg)
