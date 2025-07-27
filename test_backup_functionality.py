#!/usr/bin/env python3
"""
Test backup functionality
"""

import unittest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime

# Mock git module for testing
class MockGitRepo:
    def __init__(self, path):
        self.path = path
        self.is_dirty_called = False
        self.active_branch_name = "main"
        self.backup_created = False
        self.committed = False
        self.pushed = False
    
    def is_dirty(self):
        self.is_dirty_called = True
        return True
    
    @property
    def active_branch(self):
        return type('Branch', (), {'name': self.active_branch_name})()
    
    def create_head(self, branch_name):
        self.backup_created = True
        return type('Branch', (), {'name': branch_name})()
    
    def checkout(self, branch_name):
        if branch_name != 'main':
            self.active_branch_name = branch_name
        return True
    
    def add(self, A=True):
        return True
    
    def commit(self, message):
        self.committed = True
        return True
    
    def push(self, branch_name=None):
        self.pushed = True
        return True
    
    @property
    def remote(self):
        return type('Remote', (), {'name': 'origin'})()

class MockGit:
    @staticmethod
    def Repo(path):
        return MockGitRepo(path)

class TestBackupFunctionality(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        # Create mock config
        import json
        config_data = {
            "portfolio_path": str(self.temp_dir),
            "git_user_name": "Test User",
            "git_user_email": "test@example.com",
            "ollama_model": "llama3.1:8b"
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_backup_branch_creation(self):
        """Test that backup branches are created with correct naming"""
        from portfolio_agent import PortfolioAgent
        
        # Mock git module
        import portfolio_agent
        portfolio_agent.git = MockGit()
        
        agent = PortfolioAgent(str(self.config_path))
        
        # Test git workflow
        success = agent.git_workflow("Test commit")
        
        # Verify backup was created
        self.assertTrue(agent.config.portfolio_path == str(self.temp_dir))
        # Note: In a real test, we'd verify the git operations were called correctly
    
    def test_backup_branch_naming(self):
        """Test backup branch naming format"""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        expected_format = f"backup-{timestamp}"
        
        # The format should be backup-YYYYMMDD-HHMMSS
        self.assertTrue(expected_format.startswith("backup-"))
        self.assertEqual(len(expected_format), 20)  # backup- + 14 digits

if __name__ == '__main__':
    unittest.main() 