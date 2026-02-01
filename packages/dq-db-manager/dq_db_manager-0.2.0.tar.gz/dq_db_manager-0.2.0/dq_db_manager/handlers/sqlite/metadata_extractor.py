from dq_db_manager.handlers.base.metadata_extractor import BaseMetadataExtractor
from typing import List, Union
from datetime import datetime
import json
from dq_db_manager.utils.RDBMSHelper import extract_details, add_table_to_query, add_index_to_query, add_view_to_query, add_trigger_to_query
from dq_db_manager.models.postgres import *

class SQLiteMetadataExtractor(BaseMetadataExtractor):

    def __init__(self, connection_handler, models):
        self.connection_handler = connection_handler
        self.models = models

    def extract_table_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[TableDetail], List[dict]]:
        # SQLite uses sqlite_master to query metadata
        # table_type in SQLite is 'table' for regular tables
        table_query = """
        SELECT name AS table_name, type AS table_type
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        """
        params = []
        if table_name:
            # SQLite uses ? as placeholder
            table_query, params = add_table_to_query(query=table_query, params=params, table_name=table_name, alias="name", placeholder="?")
        return extract_details(self.connection_handler.execute_query, table_query, TableDetail, return_as_dict, *params)

    def extract_column_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ColumnDetail], List[dict]]:
        # For SQLite, we need to use PRAGMA table_info for column details
        # If no table_name is provided, we need to get all tables first
        if table_name:
            # Use PRAGMA table_info(table_name) for a specific table
            column_query = f"PRAGMA table_info({table_name})"
            raw_data = self.connection_handler.execute_query(column_query)

            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            # Map to our ColumnDetail model
            columns = []
            for row in raw_data:
                column = {
                    'column_name': row['name'],
                    'data_type': row['type'] if row['type'] else 'TEXT',  # SQLite may have empty type
                    'column_default': row['dflt_value'],
                    'is_nullable': not bool(row['notnull'])  # notnull is 1 or 0
                }
                columns.append(column)

            # Use extract_details pattern but with pre-processed data
            data_objects = [ColumnDetail(**col) for col in columns]
            if return_as_dict:
                return [dict(json.loads(data_object.model_dump_json())) for data_object in data_objects]
            return data_objects
        else:
            # Get all tables and extract columns for each
            tables = self.extract_table_details(return_as_dict=True)
            all_columns = []
            for table in tables:
                columns = self.extract_column_details(table_name=table['table_name'], return_as_dict=return_as_dict)
                all_columns.extend(columns)
            return all_columns

    def extract_constraints_details(self, table_name=None, return_as_dict: bool = False) -> Union[List[ConstraintDetail], List[dict]]:
        # SQLite constraints need to be extracted from:
        # 1. PRAGMA foreign_key_list(table_name) for foreign keys
        # 2. PRAGMA index_list(table_name) for unique constraints (via indexes)
        # 3. Parse CREATE TABLE SQL for CHECK constraints

        if table_name:
            constraints = []

            # Extract foreign keys
            fk_query = f"PRAGMA foreign_key_list({table_name})"
            fk_data = self.connection_handler.execute_query(fk_query)
            for fk in fk_data:
                constraint = {
                    'constraint_name': f"fk_{table_name}_{fk['from']}_{fk['table']}_{fk['to']}",
                    'constraint_type': 'FOREIGN KEY',
                    'source_column': fk['from'],
                    'referenced_table': fk['table'],
                    'referenced_column': fk['to'],
                }
                constraints.append(constraint)

            # Extract primary key and unique constraints from table_info
            table_info_query = f"PRAGMA table_info({table_name})"
            table_info = self.connection_handler.execute_query(table_info_query)
            pk_columns = [col['name'] for col in table_info if col['pk'] > 0]
            if pk_columns:
                constraint = {
                    'constraint_name': f"pk_{table_name}",
                    'constraint_type': 'PRIMARY KEY'
                }
                constraints.append(constraint)

            # Check for unique constraints via indexes
            index_list_query = f"PRAGMA index_list({table_name})"
            index_list = self.connection_handler.execute_query(index_list_query)
            for idx in index_list:
                if idx['unique'] == 1 and not idx['name'].startswith('sqlite_autoindex'):
                    constraint = {
                        'constraint_name': idx['name'],
                        'constraint_type': 'UNIQUE'
                    }
                    constraints.append(constraint)

            # Use extract_details pattern with pre-processed data
            data_objects = [ConstraintDetail(**con) for con in constraints]
            if return_as_dict:
                return [dict(json.loads(data_object.model_dump_json())) for data_object in data_objects]
            return data_objects
        else:
            # Get all tables and extract constraints for each
            tables = self.extract_table_details(return_as_dict=True)
            all_constraints = []
            for table in tables:
                constraints = self.extract_constraints_details(table_name=table['table_name'], return_as_dict=return_as_dict)
                all_constraints.extend(constraints)
            return all_constraints

    def extract_index_details(self, table_name=None, index_name=None, return_as_dict: bool = False) -> Union[List[IndexDetail], List[dict]]:
        # SQLite indexes can be queried from sqlite_master
        index_query = """
        SELECT name AS index_name, sql AS index_definition
        FROM sqlite_master
        WHERE type = 'index' AND name NOT LIKE 'sqlite_autoindex_%'
        """
        params = []

        if table_name:
            index_query += " AND tbl_name = ?"
            params.append(table_name)

        if index_name:
            # Use the helper but with ? placeholder
            index_query, params = add_index_to_query(query=index_query, params=params, index_name=index_name, alias="name", placeholder="?")

        # Handle case where sql might be NULL for auto-generated indexes
        raw_data = self.connection_handler.execute_query(index_query, params if params else None)
        indexes = []
        for row in raw_data:
            index = {
                'index_name': row['index_name'],
                'index_definition': row['index_definition'] if row['index_definition'] else f"Auto-generated index: {row['index_name']}"
            }
            indexes.append(index)

        data_objects = [IndexDetail(**idx) for idx in indexes]
        if return_as_dict:
            return [dict(json.loads(data_object.model_dump_json())) for data_object in data_objects]
        return data_objects

    def extract_view_details(self, view_name=None, return_as_dict: bool = False) -> Union[List[ViewDetail], List[dict]]:
        # SQLite views are in sqlite_master with type = 'view'
        view_query = """
        SELECT name AS view_name, sql AS view_definition
        FROM sqlite_master
        WHERE type = 'view'
        """
        params = []
        if view_name:
            # Use ? placeholder for SQLite
            view_query, params = add_view_to_query(query=view_query, params=params, view_name=view_name, alias="name", placeholder="?")
        return extract_details(self.connection_handler.execute_query, view_query, ViewDetail, return_as_dict, *params)

    def extract_trigger_details(self, trigger_name=None, table_name=None, return_as_dict: bool = False) -> Union[List[TriggerDetail], List[dict]]:
        # SQLite triggers are in sqlite_master with type = 'trigger'
        # We need to parse the SQL to extract event, condition, and operation
        trigger_query = """
        SELECT name AS trigger_name, tbl_name, sql
        FROM sqlite_master
        WHERE type = 'trigger'
        """
        params = []

        if table_name:
            trigger_query += " AND tbl_name = ?"
            params.append(table_name)

        if trigger_name:
            trigger_query, params = add_trigger_to_query(query=trigger_query, params=params, trigger_name=trigger_name, alias="name", placeholder="?")

        raw_data = self.connection_handler.execute_query(trigger_query, params if params else None)

        # Parse trigger SQL to extract details
        triggers = []
        for row in raw_data:
            sql = row['sql'] if row['sql'] else ""

            # Extract event (BEFORE, AFTER, INSTEAD OF)
            trigger_event = "UNKNOWN"
            if "BEFORE" in sql.upper():
                trigger_event = "BEFORE"
            elif "AFTER" in sql.upper():
                trigger_event = "AFTER"
            elif "INSTEAD OF" in sql.upper():
                trigger_event = "INSTEAD OF"

            # Extract operation (INSERT, UPDATE, DELETE)
            trigger_operation = "UNKNOWN"
            if "INSERT" in sql.upper():
                trigger_operation = "INSERT"
            elif "UPDATE" in sql.upper():
                trigger_operation = "UPDATE"
            elif "DELETE" in sql.upper():
                trigger_operation = "DELETE"

            # For condition, check if there's a WHEN clause
            trigger_condition = "NONE"
            if "WHEN" in sql.upper():
                try:
                    when_start = sql.upper().find("WHEN")
                    when_end = sql.upper().find("BEGIN", when_start)
                    if when_end > when_start:
                        trigger_condition = sql[when_start:when_end].strip()
                except:
                    trigger_condition = "WHEN clause exists"

            trigger = {
                'trigger_name': row['trigger_name'],
                'trigger_event': trigger_event,
                'trigger_condition': trigger_condition,
                'trigger_operation': trigger_operation
            }
            triggers.append(trigger)

        data_objects = [TriggerDetail(**trg) for trg in triggers]
        if return_as_dict:
            return [dict(json.loads(data_object.model_dump_json())) for data_object in data_objects]
        return data_objects

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
        # For SQLite, use the database file path as data_source_id
        complete_metadata = DataSourceMetadata(
            data_source_id=self.connection_handler.connection_details['database'],
            tables=tables,
            views=views,
            created_at=str(datetime.now()),
            updated_at=str(datetime.now())
        )

        # Serialize for MongoDB
        return dict(complete_metadata.model_dump())
