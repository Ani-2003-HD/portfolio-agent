#!/usr/bin/env python3
"""
Test file for file handlers
"""

import unittest
from pathlib import Path
import tempfile
import json
import os

from file_handlers import FileAnalyzer, PythonFileHandler, JavaScriptFileHandler, PackageJsonHandler

class TestFileHandlers(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = FileAnalyzer()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_python_file_handler(self):
        """Test Python file handler"""
        handler = PythonFileHandler()
        
        # Create a test Python file
        python_file = Path(self.temp_dir) / "test.py"
        with open(python_file, 'w') as f:
            f.write("""
import requests
import pandas as pd
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
""")
        
        # Test handler can handle the file
        self.assertTrue(handler.can_handle(python_file))
        
        # Test analysis
        analysis = handler.analyze(python_file)
        self.assertEqual(analysis.file_type, "Python")
        self.assertIn("Flask", analysis.technologies)
        self.assertIn("Pandas", analysis.technologies)
        self.assertIn("Requests", analysis.technologies)
        self.assertGreater(analysis.lines_of_code, 0)
    
    def test_javascript_file_handler(self):
        """Test JavaScript file handler"""
        handler = JavaScriptFileHandler()
        
        # Create a test JavaScript file
        js_file = Path(self.temp_dir) / "test.js"
        with open(js_file, 'w') as f:
            f.write("""
import React from 'react';
import axios from 'axios';

function App() {
    const [data, setData] = useState([]);
    
    useEffect(() => {
        axios.get('/api/data')
            .then(response => setData(response.data));
    }, []);
    
    return (
        <div>
            <h1>Hello World</h1>
        </div>
    );
}

export default App;
""")
        
        # Test handler can handle the file
        self.assertTrue(handler.can_handle(js_file))
        
        # Test analysis
        analysis = handler.analyze(js_file)
        self.assertEqual(analysis.file_type, "JavaScript/TypeScript")
        self.assertIn("React", analysis.technologies)
        self.assertIn("Axios", analysis.technologies)
        self.assertGreater(analysis.lines_of_code, 0)
    
    def test_package_json_handler(self):
        """Test package.json handler"""
        handler = PackageJsonHandler()
        
        # Create a test package.json
        package_json = Path(self.temp_dir) / "package.json"
        with open(package_json, 'w') as f:
            json.dump({
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "^4.18.0",
                    "axios": "^1.0.0"
                },
                "devDependencies": {
                    "jest": "^29.0.0",
                    "eslint": "^8.0.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "jest"
                }
            }, f)
        
        # Test handler can handle the file
        self.assertTrue(handler.can_handle(package_json))
        
        # Test analysis
        analysis = handler.analyze(package_json)
        self.assertEqual(analysis.file_type, "Package.json")
        self.assertIn("React", analysis.technologies)
        self.assertIn("Express.js", analysis.technologies)
        self.assertIn("Axios", analysis.technologies)
        self.assertIn("Jest", analysis.technologies)
        self.assertIn("ESLint", analysis.technologies)
    
    def test_file_analyzer(self):
        """Test the main file analyzer"""
        # Create a simple project structure
        project_dir = Path(self.temp_dir) / "test-project"
        project_dir.mkdir()
        
        # Create some test files
        (project_dir / "main.py").write_text("import requests\nprint('Hello')")
        (project_dir / "app.js").write_text("import React from 'react';\nconsole.log('Hello');")
        (project_dir / "package.json").write_text(json.dumps({
            "name": "test",
            "dependencies": {"react": "^18.0.0"}
        }))
        
        # Test analysis
        result = self.analyzer.analyze_project(project_dir)
        
        self.assertGreater(result['files_analyzed'], 0)
        self.assertGreater(result['total_lines'], 0)
        self.assertIn('React', result['technologies'])
        self.assertIn('Requests', result['technologies'])

if __name__ == '__main__':
    unittest.main() 