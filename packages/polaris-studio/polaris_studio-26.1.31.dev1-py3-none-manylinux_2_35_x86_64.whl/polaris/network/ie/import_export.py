# Copyright (c) 2026, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import os
import logging

from polaris.network.ie.gmns.export_gmns import export_to_gmns
from polaris.network.ie.gmns.import_gmns import import_from_gmns
from polaris.utils.database.db_utils import read_and_close
from polaris.utils.database.import_export import ImportExport
from polaris.utils.database.standard_database import DatabaseType


class NetworkImportExport(ImportExport):
    """
    This class allows for importing and exporting to the GMNS format.
    """

    def __init__(self, supply_database_path: os.PathLike):
        super().__init__(supply_database_path, db_type=DatabaseType.Supply)

    def foo(self):
        return self.path_to_database

    def dump(self, *args, **kwargs) -> None:
        """Creates a folder and dumps all tables in the database to CSV files.

        See parent class ImportExport.dump for full documentation.
        Note: spatial is always set to True for NetworkImportExport.
        """
        if "spatial" in kwargs:
            logging.warning("spatial parameter is ignored for NetworkImportExport, always using spatial=True")
            kwargs.pop("spatial")
        super().dump(*args, **kwargs, spatial=True)

    def from_gmns(self, gmns_folder: str, crs: str):
        """Imports the network data from the GMNS format

        Args:
            *gmns_folder* (:obj:`str`): Folder where the GMNS files are located
            *crs* (:obj:`str`): CRS of the exported dataset in readable format by PyProj (e.g. 'epsg:4326')"""
        import_from_gmns(gmns_folder, crs, self.path_to_database)

    def to_gmns(self, gmns_folder: str, crs: str):
        """Exports the network data to the GMNS format

        Args:
            *gmns_folder* (:obj:`str`): Folder where the GMNS files are to be placed
            *crs* (:obj:`str`): CRS of the exported dataset in readable format by PyProj (e.g. 'epsg:4326')"""
        with read_and_close(self.path_to_database, spatial=True) as conn:
            export_to_gmns(gmns_folder, crs, conn, self.path_to_database)

    def __run_consistency(self):
        from polaris.network.consistency.consistency import Consistency

        Consistency(self.path_to_database).enforce()
