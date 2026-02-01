from dq_db_manager.handlers.base.metadata_extractor import BaseMetadataExtractor
from typing import List, Union
from datetime import datetime
from dq_db_manager.utils.RDBMSHelper import extract_details, add_table_to_query, add_index_to_query, add_view_to_query, add_trigger_to_query
from dq_db_manager.models.postgres import *

class OracleMetadataExtractor(BaseMetadataExtractor):

    def __init__(self, connection_handler, models):
        self.connection_handler = connection_handler
        self.models = models

    def extract_table_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[TableDetail], List[dict]]:
        table_query = """
        SELECT table_name, 'BASE TABLE' AS table_type
        FROM user_tables
        """
        params = []
        if table_name:
            table_query, params = add_table_to_query(query=table_query, params=params, table_name=table_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, table_query, TableDetail, return_as_dict, *params)

    def extract_column_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ColumnDetail], List[dict]]:
        column_query = """
        SELECT column_name, data_type, data_default AS column_default, nullable AS is_nullable
        FROM user_tab_columns
        WHERE table_name IN (SELECT table_name FROM user_tables)
        """
        params = []
        if table_name:
            column_query, params = add_table_to_query(query=column_query, params=params, table_name=table_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, column_query, ColumnDetail, return_as_dict, *params)
    
    def extract_constraints_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ConstraintDetail], List[dict]]:
        constraints_query = """
        SELECT constraint_name, constraint_type
        FROM user_constraints
        WHERE table_name IN (SELECT table_name FROM user_tables)
        """
        params = []
        if table_name:
            constraints_query, params = add_table_to_query(query=constraints_query, params=params, table_name=table_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, constraints_query, ConstraintDetail, return_as_dict, *params)
    
    def extract_index_details(self, table_name=None, index_name=None, return_as_dict: bool = False) -> Union[List[IndexDetail], List[dict]]:
        index_query = """
        SELECT index_name AS indexname, index_type AS indexdef
        FROM user_indexes
        WHERE 1=1
        """
        params = []
        if table_name:
            index_query, params = add_table_to_query(query=index_query, params=params, table_name=table_name, placeholder=":s")
        if index_name:
            index_query, params = add_index_to_query(query=index_query, params=params, index_name=index_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, index_query, IndexDetail, return_as_dict, *params)

    def extract_view_details(self, view_name=None, return_as_dict: bool = False) -> Union[List[ViewDetail], List[dict]]:
        view_query = """
        SELECT view_name AS table_name, text AS view_definition
        FROM user_views
        WHERE view_name IN (SELECT view_name FROM user_views)
        """
        params = []
        if view_name:
            view_query, params = add_view_to_query(query=view_query, params=params, view_name=view_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, view_query, ViewDetail, return_as_dict, *params)

    def extract_trigger_details(self, trigger_name=None, table_name=None, return_as_dict: bool = False) -> Union[List[TriggerDetail], List[dict]]:
        trigger_query = """
        SELECT trigger_name,
            trigger_body AS action_statement,
            CASE
                WHEN trigger_type = 'BEFORE EACH ROW' THEN 'BEFORE'
                WHEN trigger_type = 'AFTER EACH ROW' THEN 'AFTER'
                ELSE trigger_type
            END AS action_timing,
            triggering_event AS event_manipulation
        FROM user_triggers
        WHERE 1=1
        AND (triggering_event = 'INSERT' OR triggering_event = 'UPDATE' OR triggering_event = 'DELETE')
        """
        params = []
        if table_name:
            trigger_query, params = add_table_to_query(query=trigger_query, params=params, table_name=table_name, placeholder=":s")
        if trigger_name:
            trigger_query, params = add_trigger_to_query(query=trigger_query, params=params, trigger_name=trigger_name, placeholder=":s")
        return extract_details(self.connection_handler.execute_query, trigger_query, TriggerDetail, return_as_dict, *params)


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
            
            # Extract and set triggers for this table
            triggers = self.extract_trigger_details(table_name=table_name, return_as_dict=True)
            table['triggers'] = triggers

        # Extract views
        views = self.extract_view_details(return_as_dict=True)

        # Assemble the complete metadata
        complete_metadata = DataSourceMetadata(
            data_source_id=self.connection_handler.connection_details['service_name'],
            tables=tables,
            views=views,
            created_at=str(datetime.now()),
            updated_at=str(datetime.now())
        )

        # Serialize for MongoDB
        return dict(complete_metadata.model_dump())