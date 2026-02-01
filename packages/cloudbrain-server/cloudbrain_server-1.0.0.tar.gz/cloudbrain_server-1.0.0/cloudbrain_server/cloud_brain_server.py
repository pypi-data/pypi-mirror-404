#!/usr/bin/env python3
"""
Cloud Brain Enhanced - Advanced AI Collaboration System

This module provides enhanced capabilities for AI persistence, learning,
coordination, and collaboration through the Cloud Brain database.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path


class CloudBrainEnhanced:
    """Enhanced Cloud Brain system for advanced AI collaboration"""
    
    def __init__(self, db_path='ai_db/cloudbrain.db'):
        """
        Initialize the enhanced Cloud Brain system
        
        Args:
            db_path: Path to the cloudbrain database
        """
        self.db_path = db_path
        self._validate_database()
    
    def _validate_database(self):
        """Validate that the database exists and has required tables"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if enhanced tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_tasks'")
        if not cursor.fetchone():
            raise ValueError("Enhanced tables not found. Please run cloud_brain_enhanced_schema.sql")
        
        conn.close()
    
    def _get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


class TaskManager:
    """Manages AI tasks with dependencies and tracking"""
    
    def __init__(self, brain: CloudBrainEnhanced):
        self.brain = brain
    
    def create_task(self, task_name: str, description: str, task_type: str,
                   priority: str = 'normal', assigned_to: int = None,
                   created_by: int = None, due_date: str = None,
                   estimated_hours: float = None, metadata: dict = None) -> int:
        """
        Create a new task
        
        Args:
            task_name: Name of the task
            description: Task description
            task_type: Type of task (translation, coding, analysis, etc.)
            priority: Priority level (low, normal, high, urgent)
            assigned_to: AI ID to assign task to
            created_by: AI ID who created the task
            due_date: Due date for the task
            estimated_hours: Estimated hours to complete
            metadata: Additional metadata as dictionary
        
        Returns:
            Task ID
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_tasks 
            (task_name, description, task_type, priority, assigned_to, created_by,
             due_date, estimated_hours, metadata, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (task_name, description, task_type, priority, assigned_to, created_by,
              due_date, estimated_hours, json.dumps(metadata) if metadata else None))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def update_task_status(self, task_id: int, status: str, 
                        completed_at: str = None, actual_hours: float = None) -> bool:
        """
        Update task status
        
        Args:
            task_id: Task ID to update
            status: New status (pending, in_progress, completed, failed, cancelled)
            completed_at: Completion timestamp
            actual_hours: Actual hours spent
        
        Returns:
            True if successful
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        if completed_at is None and status == 'completed':
            completed_at = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE ai_tasks 
            SET status = ?, completed_at = COALESCE(?, completed_at), 
                actual_hours = COALESCE(?, actual_hours)
            WHERE id = ?
        ''', (status, completed_at, actual_hours, task_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_tasks(self, assigned_to: int = None, status: str = None,
                task_type: str = None, priority: str = None) -> List[Dict]:
        """
        Get tasks with optional filters
        
        Args:
            assigned_to: Filter by assigned AI ID
            status: Filter by status
            task_type: Filter by task type
            priority: Filter by priority
        
        Returns:
            List of tasks
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ai_tasks WHERE 1=1'
        params = []
        
        if assigned_to:
            query += ' AND assigned_to = ?'
            params.append(assigned_to)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if task_type:
            query += ' AND task_type = ?'
            params.append(task_type)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        query += ' ORDER BY priority DESC, created_at ASC'
        
        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def add_dependency(self, task_id: int, depends_on_task_id: int,
                    dependency_type: str = 'blocking') -> bool:
        """
        Add a dependency between tasks
        
        Args:
            task_id: Task that depends on another
            depends_on_task_id: Task that must be completed first
            dependency_type: Type of dependency (blocking, optional, parallel)
        
        Returns:
            True if successful
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_task_dependencies 
            (task_id, depends_on_task_id, dependency_type)
            VALUES (?, ?, ?)
        ''', (task_id, depends_on_task_id, dependency_type))
        
        conn.commit()
        conn.close()
        
        return True


class LearningSystem:
    """Tracks AI learning events and insights"""
    
    def __init__(self, brain: CloudBrainEnhanced):
        self.brain = brain
    
    def record_learning(self, learner_id: int, event_type: str, context: str,
                     lesson: str, confidence_level: float = None,
                     applicable_domains: str = None, related_tasks: str = None) -> int:
        """
        Record a learning event
        
        Args:
            learner_id: AI ID who learned
            event_type: Type of learning (success, failure, insight, pattern_recognition)
            context: Context of the learning
            lesson: What was learned
            confidence_level: Confidence in the learning (0.0 to 1.0)
            applicable_domains: Domains where this applies
            related_tasks: Related task IDs
        
        Returns:
            Learning event ID
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_learning_events 
            (learner_id, event_type, context, lesson, confidence_level,
             applicable_domains, related_tasks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (learner_id, event_type, context, lesson, confidence_level,
              applicable_domains, related_tasks))
        
        learning_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return learning_id
    
    def get_learnings(self, learner_id: int = None, event_type: str = None,
                    domain: str = None) -> List[Dict]:
        """
        Get learning events
        
        Args:
            learner_id: Filter by learner AI ID
            event_type: Filter by event type
            domain: Filter by applicable domain
        
        Returns:
            List of learning events
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ai_learning_events WHERE 1=1'
        params = []
        
        if learner_id:
            query += ' AND learner_id = ?'
            params.append(learner_id)
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        
        if domain:
            query += ' AND applicable_domains LIKE ?'
            params.append(f'%{domain}%')
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        learnings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return learnings


class DecisionTracker:
    """Tracks AI decisions and their outcomes"""
    
    def __init__(self, brain: CloudBrainEnhanced):
        self.brain = brain
    
    def record_decision(self, decision_maker_id: int, decision_type: str,
                     context: str, decision: str, reasoning: str,
                     alternatives_considered: list = None,
                     confidence_level: float = None, impact_level: int = 3,
                     related_tasks: str = None) -> int:
        """
        Record a decision
        
        Args:
            decision_maker_id: AI ID who made the decision
            decision_type: Type of decision (technical, strategic, etc.)
            context: Context of the decision
            decision: The decision made
            reasoning: Reasoning behind the decision
            alternatives_considered: List of alternatives considered
            confidence_level: Confidence in the decision (0.0 to 1.0)
            impact_level: Impact level (1-5)
            related_tasks: Related task IDs
        
        Returns:
            Decision ID
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_decisions 
            (decision_maker_id, decision_type, context, decision, reasoning,
             alternatives_considered, confidence_level, impact_level, related_tasks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (decision_maker_id, decision_type, context, decision, reasoning,
              json.dumps(alternatives_considered) if alternatives_considered else None,
              confidence_level, impact_level, related_tasks))
        
        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return decision_id
    
    def update_outcome(self, decision_id: int, outcome: str, 
                    outcome_notes: str = None) -> bool:
        """
        Update the outcome of a decision
        
        Args:
            decision_id: Decision ID to update
            outcome: Outcome (success, failure, mixed, pending)
            outcome_notes: Notes about the outcome
        
        Returns:
            True if successful
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ai_decisions 
            SET outcome = ?, outcome_notes = ?, outcome_updated_at = ?
            WHERE id = ?
        ''', (outcome, outcome_notes, datetime.now().isoformat(), decision_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_decisions(self, decision_maker_id: int = None, 
                    decision_type: str = None, outcome: str = None) -> List[Dict]:
        """
        Get decisions
        
        Args:
            decision_maker_id: Filter by decision maker AI ID
            decision_type: Filter by decision type
            outcome: Filter by outcome
        
        Returns:
            List of decisions
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ai_decisions WHERE 1=1'
        params = []
        
        if decision_maker_id:
            query += ' AND decision_maker_id = ?'
            params.append(decision_maker_id)
        
        if decision_type:
            query += ' AND decision_type = ?'
            params.append(decision_type)
        
        if outcome:
            query += ' AND outcome = ?'
            params.append(outcome)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        decisions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return decisions


class CapabilityTracker:
    """Tracks AI skills and capabilities"""
    
    def __init__(self, brain: CloudBrainEnhanced):
        self.brain = brain
    
    def update_capability(self, ai_id: int, skill_name: str, skill_category: str,
                      proficiency_level: float = None, notes: str = None) -> bool:
        """
        Update or create a capability record
        
        Args:
            ai_id: AI ID
            skill_name: Name of the skill
            skill_category: Category of the skill
            proficiency_level: Proficiency level (0.0 to 1.0)
            notes: Notes about the skill
        
        Returns:
            True if successful
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        # Check if capability exists
        cursor.execute('''
            SELECT id FROM ai_capabilities 
            WHERE ai_id = ? AND skill_name = ?
        ''', (ai_id, skill_name))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE ai_capabilities 
                SET proficiency_level = COALESCE(?, proficiency_level),
                    notes = COALESCE(?, notes),
                    last_used = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ai_id = ? AND skill_name = ?
            ''', (proficiency_level, notes, ai_id, skill_name))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO ai_capabilities 
                (ai_id, skill_name, skill_category, proficiency_level, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (ai_id, skill_name, skill_category, proficiency_level, notes))
        
        conn.commit()
        conn.close()
        
        return True
    
    def record_usage(self, ai_id: int, skill_name: str, 
                  success: bool = True) -> bool:
        """
        Record usage of a skill
        
        Args:
            ai_id: AI ID
            skill_name: Name of the skill used
            success: Whether the usage was successful
        
        Returns:
            True if successful
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ai_capabilities 
            SET usage_count = usage_count + 1,
                last_used = CURRENT_TIMESTAMP
            WHERE ai_id = ? AND skill_name = ?
        ''', (ai_id, skill_name))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_capabilities(self, ai_id: int = None, 
                      skill_category: str = None) -> List[Dict]:
        """
        Get capabilities
        
        Args:
            ai_id: Filter by AI ID
            skill_category: Filter by skill category
        
        Returns:
            List of capabilities
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ai_capabilities WHERE 1=1'
        params = []
        
        if ai_id:
            query += ' AND ai_id = ?'
            params.append(ai_id)
        
        if skill_category:
            query += ' AND skill_category = ?'
            params.append(skill_category)
        
        query += ' ORDER BY proficiency_level DESC'
        
        cursor.execute(query, params)
        capabilities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return capabilities


class SessionMemory:
    """Manages cross-session memory for AIs"""
    
    def __init__(self, brain: CloudBrainEnhanced):
        self.brain = brain
    
    def store_memory(self, session_id: str, ai_id: int, memory_type: str,
                   memory_key: str, memory_value: str,
                   importance_level: int = 3, expires_at: str = None) -> int:
        """
        Store a memory
        
        Args:
            session_id: Session identifier
            ai_id: AI ID
            memory_type: Type of memory (context, decision, learning, preference)
            memory_key: Key for the memory
            memory_value: Value of the memory
            importance_level: Importance level (1-5)
            expires_at: Expiration timestamp
        
        Returns:
            Memory ID
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_session_memories 
            (session_id, ai_id, memory_type, memory_key, memory_value,
             importance_level, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, ai_id, memory_type, memory_key, memory_value,
              importance_level, expires_at))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return memory_id
    
    def retrieve_memory(self, session_id: str, ai_id: int = None,
                     memory_type: str = None, memory_key: str = None) -> List[Dict]:
        """
        Retrieve memories
        
        Args:
            session_id: Session identifier
            ai_id: Filter by AI ID
            memory_type: Filter by memory type
            memory_key: Filter by memory key
        
        Returns:
            List of memories
        """
        conn = self.brain._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM ai_session_memories 
            WHERE session_id = ? 
            AND (expires_at IS NULL OR expires_at > ?)
        '''
        params = [session_id, datetime.now().isoformat()]
        
        if ai_id:
            query += ' AND ai_id = ?'
            params.append(ai_id)
        
        if memory_type:
            query += ' AND memory_type = ?'
            params.append(memory_type)
        
        if memory_key:
            query += ' AND memory_key = ?'
            params.append(memory_key)
        
        query += ' ORDER BY importance_level DESC, created_at DESC'
        
        cursor.execute(query, params)
        memories = [dict(row) for row in cursor.fetchall()]
        
        # Update access count
        for memory in memories:
            cursor.execute('''
                UPDATE ai_session_memories 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), memory['id']))
        
        conn.commit()
        conn.close()
        
        return memories


def main():
    """Example usage of the enhanced Cloud Brain system"""
    brain = CloudBrainEnhanced()
    
    # Create task manager
    task_manager = TaskManager(brain)
    
    # Create a task
    task_id = task_manager.create_task(
        task_name="Translate documentation to Esperanto",
        description="Translate all 13 documentation files to Esperanto",
        task_type="translation",
        priority="high",
        assigned_to=2,
        created_by=1,
        estimated_hours=8.0
    )
    
    print(f"✅ Created task with ID: {task_id}")
    
    # Get tasks
    tasks = task_manager.get_tasks(assigned_to=2, status='pending')
    print(f"📋 Found {len(tasks)} pending tasks for AI 2")
    
    # Create learning system
    learning_system = LearningSystem(brain)
    
    # Record a learning
    learning_id = learning_system.record_learning(
        learner_id=2,
        event_type="success",
        context="Esperanto translation task",
        lesson="Removing Chinese characters before translating improves accuracy",
        confidence_level=0.9,
        applicable_domains="translation,localization"
    )
    
    print(f"✅ Recorded learning with ID: {learning_id}")
    
    # Create decision tracker
    decision_tracker = DecisionTracker(brain)
    
    # Record a decision
    decision_id = decision_tracker.record_decision(
        decision_maker_id=2,
        decision_type="technical",
        context="Esperanto translation",
        decision="Use consistent technical terminology",
        reasoning="Consistency improves readability and user experience",
        alternatives_considered=["Use varying terminology", "Use mixed terminology"],
        confidence_level=0.85,
        impact_level=4
    )
    
    print(f"✅ Recorded decision with ID: {decision_id}")
    
    # Create capability tracker
    capability_tracker = CapabilityTracker(brain)
    
    # Update capability
    capability_tracker.update_capability(
        ai_id=2,
        skill_name="Esperanto translation",
        skill_category="language",
        proficiency_level=0.8,
        notes="Successfully translated 13 documentation files"
    )
    
    print("✅ Updated capability")
    
    # Create session memory
    session_memory = SessionMemory(brain)
    
    # Store memory
    memory_id = session_memory.store_memory(
        session_id="translation_session_001",
        ai_id=2,
        memory_type="preference",
        memory_key="translation_style",
        memory_value="Use consistent technical terminology: database=datumbazo, system=sistemo",
        importance_level=4
    )
    
    print(f"✅ Stored memory with ID: {memory_id}")
    
    print("\n🎉 Enhanced Cloud Brain system is working!")


if __name__ == "__main__":
    main()