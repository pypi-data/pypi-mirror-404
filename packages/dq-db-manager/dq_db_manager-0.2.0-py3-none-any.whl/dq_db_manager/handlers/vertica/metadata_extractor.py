from dq_db_manager.handlers.base.metadata_extractor import BaseMetadataExtractor
from typing import List, Union
from datetime import datetime
from dq_db_manager.utils.RDBMSHelper import extract_details, add_table_to_query, add_index_to_query, add_view_to_query, create_data_source_id
from dq_db_manager.models.postgres import *

class VerticaMetadataExtractor(BaseMetadataExtractor):

    def __init__(self, connection_handler, models):
        self.connection_handler = connection_handler
        self.models = models

    def extract_table_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[TableDetail], List[dict]]:
        table_query = "SELECT table_name, 'BASE TABLE' AS table_type FROM v_catalog.tables WHERE 1=1 "
        params = []
        if table_name:
            table_query, params = add_table_to_query(query=table_query, params=params, table_name=table_name)
        return extract_details(self.connection_handler.execute_query, table_query, TableDetail, return_as_dict, *params)

    def extract_column_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ColumnDetail], List[dict]]:
        column_query = """
        SELECT column_name, data_type, column_default, is_nullable
        FROM v_catalog.columns
        WHERE 1=1
        """
        params = []
        if table_name:
            column_query, params = add_table_to_query(query=column_query, params=params, table_name=table_name)
        return extract_details(self.connection_handler.execute_query, column_query, ColumnDetail, return_as_dict, *params)
    
    def extract_constraints_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ConstraintDetail], List[dict]]:
        constraints_query = """
        SELECT cc.constraint_name, cc.constraint_type
        FROM v_catalog.constraint_columns cc
        JOIN v_catalog.tables t ON cc.table_id = t.table_id
        """
        params = []
        if table_name:
            constraints_query, params = add_table_to_query(query=constraints_query, params=params, table_name=table_name, alias="t.table_name")
        return extract_details(self.connection_handler.execute_query, constraints_query, ConstraintDetail, return_as_dict, *params)
    
    def extract_index_details(self, table_name=None, index_name=None, return_as_dict: bool = False) -> Union[List[IndexDetail], List[dict]]:
        index_query = """
        SELECT projection_basename, segment_expression
        FROM projections
        WHERE 1=1
        """
        params = []
        if table_name:
            index_query, params = add_table_to_query(query=index_query, params=params, table_name=table_name, alias="anchor_table_name")
        if index_name:
            index_query, params = add_index_to_query(query=index_query, params=params, index_name=index_name)
        return extract_details(self.connection_handler.execute_query, index_query, IndexDetail, return_as_dict, *params)

    def extract_view_details(self, view_name=None, return_as_dict: bool = False) -> Union[List[ViewDetail], List[dict]]:
        view_query = """
        SELECT table_name, view_definition 
        FROM v_catalog.views
        """
        params = []
        if view_name:
            view_query, params = add_view_to_query(query=view_query, params=params, view_name=view_name)
        return extract_details(self.connection_handler.execute_query, view_query, ViewDetail, return_as_dict, *params)

    def get_complete_metadata(self):
        # Extract all tables first
        tables = self.extract_table_details(return_as_dict=True)

        # For each table, enrich it with columns, constraints, indexes, and triggers
        for table in tables:
            table_name = table['table_name']
            
            # Extract and set columns for this table
            columns = self.extract_column_details(table_name=table_name, return_as_dict=True)
            table['columns'] = columns
            
            # Extract and set constraints for this table
            constraints = self.extract_constraints_details(table_name=table_name, return_as_dict=True)
            table['constraints'] = constraints
            
            # Extract and set indexes for this table
            indexes = self.extract_index_details(table_name=table_name, return_as_dict=True)
            table['indexes'] = indexes

        # Extract views
        views = self.extract_view_details(return_as_dict=True)

        # Assemble the complete metadata

        complete_metadata = DataSourceMetadata(
            data_source_id=create_data_source_id(self.connection_handler.connection_details),
            tables=tables,
            views=views,
            created_at=str(datetime.now()),
            updated_at=str(datetime.now())
        )

        # Serialize for MongoDB
        return dict(complete_metadata.model_dump())



    # Function to extract trigger details

    # TODO: In Vertica, there isn't a direct equivalent to 
    # PostgreSQL's information_schema.triggers view as Vertica doesn't 
    # support triggers in the same way. Instead, Vertica provides a mechanism 
    # called Flex Tables for capturing external events and processing them asynchronously.

    # def extract_trigger_details(self, trigger_name=None):
    #     trigger_query = """

    #     """
    #     params = []

    #     if trigger_name:
    #         trigger_query += " AND trigger_name = %s"
    #         params.append(trigger_name)

    #     return self.connection_handler.execute_query(trigger_query, tuple(params))

    # ... other metadata extraction met
