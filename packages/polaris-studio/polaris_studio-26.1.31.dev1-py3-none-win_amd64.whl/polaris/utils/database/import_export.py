# Copyright (c) 2026, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import os
from pathlib import Path
from polaris.utils.database.database_dumper import dump_database_to_csv
from polaris.utils.database.db_utils import read_and_close
from polaris.project.project_restorer import create_db_from_csv
from polaris.utils.database.standard_database import DatabaseType
from polaris.utils.signals import SIGNAL


class ImportExport:
    """
    This class allows for importing and exporting databases from and to standard CSV dumps.
    """

    loading = SIGNAL(object)

    def __init__(self, path_to_file: os.PathLike, db_type: DatabaseType):
        self.path_to_database = Path(path_to_file)
        self.db_type = db_type

    def dump(
        self, folder_name: str, tables=None, include_patterns=None, target_crs=None, extension="csv", spatial=False
    ) -> None:
        """Creates a folder and dumps all tables in the database to CSV files

        Args:
            *folder_name* (:obj:`str`): Folder where the dump files are to be placed

            *tables* (:obj:`list`, `Optional`): List of tables to be dumped. If None, all tables are dumped. Defaults to None

            *include_patterns* (:obj:`list`, `Optional`): List of table name patterns to be dumped. If None, no patterns will be enforced. Defaults to None. Cannot be provided when providing a list of *tables* to dump

            *target_crs* (:obj:`int`, `Optional`): The desired CRS for the dumped files. If None, the original CRS is used. Defaults to None

            *extension* (:obj:`str`, `Optional`): The extension of the dumped files. Defaults to 'csv'. The preferred alternative is "parquet"

            *spatial* (:obj:`bool`, `Optional`): Reads database as spatial or not. Defaults to False
        """

        folder = Path(folder_name)
        folder = folder if folder.is_absolute() else (self.path_to_database.parent / folder).resolve()
        with read_and_close(self.path_to_database, spatial=spatial) as conn:
            dump_database_to_csv(
                conn,
                folder,
                signal=self.loading,
                table_list=tables,
                include_patterns=include_patterns,
                target_crs=target_crs,
                ext=extension,
            )

    def restore(self, folder_name: os.PathLike, overwrite=False, jumpstart=False, database_name=None) -> None:
        """Reloads the database from a previous csv dump

        Args:
            *folder_name* (:obj:`str`): Folder where the dump files are located
            *overwrite* (:obj:`bool`): Overwrite the existing database. Defaults to False.
            *jumpstart* (:obj:`bool`): Copies base sql already initialized with spatialite base tables. It saves about
                                       a minute of runtime.
        """

        if not os.path.isdir(folder_name):
            raise FileNotFoundError

        fldr = self.path_to_database.parent
        file_to_create = fldr / database_name if database_name else self.path_to_database
        create_db_from_csv(file_to_create, folder_name, self.db_type, self.loading, overwrite, jumpstart)
