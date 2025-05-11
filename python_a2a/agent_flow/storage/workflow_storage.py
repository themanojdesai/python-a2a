"""
Workflow storage service for persisting workflows.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..models.workflow import Workflow


class WorkflowStorage:
    """
    Base storage service interface for workflows.
    
    This abstract class defines the interface for workflow storage services.
    Implementations should provide mechanisms to save, load, list, and delete
    workflows.
    """
    
    def save_workflow(self, workflow: Workflow) -> str:
        """
        Save a workflow to storage.
        
        Args:
            workflow: The workflow to save
            
        Returns:
            The ID of the saved workflow
        """
        raise NotImplementedError("Storage service must implement save_workflow")
    
    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow from storage.
        
        Args:
            workflow_id: ID of the workflow to load
            
        Returns:
            The workflow if found, None otherwise
        """
        raise NotImplementedError("Storage service must implement load_workflow")
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows in storage.
        
        Returns:
            List of workflow metadata dictionaries
        """
        raise NotImplementedError("Storage service must implement list_workflows")
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow from storage.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError("Storage service must implement delete_workflow")


class FileWorkflowStorage(WorkflowStorage):
    """
    File-based storage service for workflows.
    
    This implementation stores workflows as JSON files in a directory.
    """
    
    def __init__(self, storage_dir: str):
        """
        Initialize file-based workflow storage.
        
        Args:
            storage_dir: Directory to store workflow files
        """
        self.storage_dir = storage_dir
        
        # Create directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Create index file if it doesn't exist
        self.index_file = os.path.join(storage_dir, "index.json")
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w") as f:
                json.dump({"workflows": []}, f)
    
    def save_workflow(self, workflow: Workflow) -> str:
        """
        Save a workflow to a file.
        
        Args:
            workflow: The workflow to save
            
        Returns:
            The ID of the saved workflow
        """
        # Update timestamps
        workflow.updated_at = datetime.now()
        
        # Serialize workflow to JSON
        workflow_data = workflow.to_dict()
        workflow_id = workflow.id
        
        # Save workflow file
        file_path = os.path.join(self.storage_dir, f"{workflow_id}.json")
        with open(file_path, "w") as f:
            json.dump(workflow_data, f, indent=2, default=str)
        
        # Update index
        self._update_index(workflow)
        
        return workflow_id
    
    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow from a file.
        
        Args:
            workflow_id: ID of the workflow to load
            
        Returns:
            The workflow if found, None otherwise
        """
        file_path = os.path.join(self.storage_dir, f"{workflow_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r") as f:
                workflow_data = json.load(f)
            
            workflow = Workflow.from_dict(workflow_data)
            return workflow
        except Exception as e:
            print(f"Error loading workflow {workflow_id}: {e}")
            return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows in the storage directory.
        
        Returns:
            List of workflow metadata dictionaries
        """
        try:
            with open(self.index_file, "r") as f:
                index_data = json.load(f)
            
            return index_data.get("workflows", [])
        except Exception as e:
            print(f"Error loading workflow index: {e}")
            return []
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow file.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if deleted, False if not found
        """
        file_path = os.path.join(self.storage_dir, f"{workflow_id}.json")
        
        if not os.path.exists(file_path):
            return False
        
        try:
            # Remove file
            os.remove(file_path)
            
            # Update index
            self._remove_from_index(workflow_id)
            
            return True
        except Exception as e:
            print(f"Error deleting workflow {workflow_id}: {e}")
            return False
    
    def _update_index(self, workflow: Workflow) -> None:
        """
        Update the workflow index.
        
        Args:
            workflow: The workflow to index
        """
        try:
            # Load current index
            with open(self.index_file, "r") as f:
                index_data = json.load(f)
            
            workflows = index_data.get("workflows", [])
            
            # Check if workflow is already in index
            found = False
            for i, entry in enumerate(workflows):
                if entry.get("id") == workflow.id:
                    # Update existing entry
                    workflows[i] = {
                        "id": workflow.id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "created_at": workflow.created_at.isoformat(),
                        "updated_at": workflow.updated_at.isoformat(),
                        "version": workflow.version
                    }
                    found = True
                    break
            
            if not found:
                # Add new entry
                workflows.append({
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat(),
                    "version": workflow.version
                })
            
            # Save updated index
            with open(self.index_file, "w") as f:
                json.dump({"workflows": workflows}, f, indent=2)
        
        except Exception as e:
            print(f"Error updating workflow index: {e}")
    
    def _remove_from_index(self, workflow_id: str) -> None:
        """
        Remove a workflow from the index.
        
        Args:
            workflow_id: ID of the workflow to remove
        """
        try:
            # Load current index
            with open(self.index_file, "r") as f:
                index_data = json.load(f)
            
            workflows = index_data.get("workflows", [])
            
            # Filter out the workflow
            workflows = [w for w in workflows if w.get("id") != workflow_id]
            
            # Save updated index
            with open(self.index_file, "w") as f:
                json.dump({"workflows": workflows}, f, indent=2)
        
        except Exception as e:
            print(f"Error updating workflow index: {e}")


class SqliteWorkflowStorage(WorkflowStorage):
    """
    SQLite-based storage service for workflows.
    
    This implementation stores workflows in an SQLite database.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite-based workflow storage.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create workflows table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            version TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_workflow(self, workflow: Workflow) -> str:
        """
        Save a workflow to the database.
        
        Args:
            workflow: The workflow to save
            
        Returns:
            The ID of the saved workflow
        """
        # Update timestamps
        workflow.updated_at = datetime.now()
        
        # Serialize workflow to JSON
        workflow_data = workflow.to_json()
        workflow_id = workflow.id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if workflow exists
        cursor.execute(
            "SELECT id FROM workflows WHERE id = ?",
            (workflow_id,)
        )
        
        if cursor.fetchone():
            # Update existing workflow
            cursor.execute(
                """
                UPDATE workflows 
                SET name = ?, description = ?, data = ?, updated_at = ?, version = ? 
                WHERE id = ?
                """,
                (
                    workflow.name,
                    workflow.description,
                    workflow_data,
                    workflow.updated_at.isoformat(),
                    workflow.version,
                    workflow_id
                )
            )
        else:
            # Insert new workflow
            cursor.execute(
                """
                INSERT INTO workflows (id, name, description, data, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    workflow.name,
                    workflow.description,
                    workflow_data,
                    workflow.created_at.isoformat(),
                    workflow.updated_at.isoformat(),
                    workflow.version
                )
            )
        
        conn.commit()
        conn.close()
        
        return workflow_id
    
    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow from the database.
        
        Args:
            workflow_id: ID of the workflow to load
            
        Returns:
            The workflow if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data FROM workflows WHERE id = ?",
            (workflow_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        try:
            workflow_data = row[0]
            workflow = Workflow.from_json(workflow_data)
            return workflow
        except Exception as e:
            print(f"Error loading workflow {workflow_id}: {e}")
            return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows in the database.
        
        Returns:
            List of workflow metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, name, description, created_at, updated_at, version 
            FROM workflows
            ORDER BY updated_at DESC
            """
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        workflows = []
        for row in rows:
            workflows.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "version": row[5]
            })
        
        return workflows
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow from the database.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM workflows WHERE id = ?",
            (workflow_id,)
        )
        
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute(
            "DELETE FROM workflows WHERE id = ?",
            (workflow_id,)
        )
        
        conn.commit()
        conn.close()
        
        return True