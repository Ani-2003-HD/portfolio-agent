#!/usr/bin/env python3
"""
File Handlers - File parsing modules for portfolio projects
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import dataclass

@dataclass
class FileAnalysis:
    """Analysis result for a file"""
    file_type: str
    content_summary: str
    key_components: List[str]
    technologies: List[str]
    complexity_score: int  # 1-10
    lines_of_code: int

class FileHandler:
    """Base class for file handlers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file"""
        raise NotImplementedError
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        """Analyze the file and return analysis results"""
        raise NotImplementedError
    
    def extract_technologies(self, content: str) -> List[str]:
        """Extract technologies from file content"""
        raise NotImplementedError

class PythonFileHandler(FileHandler):
    """Handler for Python files"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == '.py'
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Extract imports
            imports = re.findall(r'^(?:from\s+(\w+)|import\s+(\w+))', content, re.MULTILINE)
            key_components = [imp[0] or imp[1] for imp in imports if any(imp)]
            
            # Detect frameworks and libraries
            technologies = self.extract_technologies(content)
            
            # Simple complexity scoring
            complexity_score = min(10, max(1, 
                len(re.findall(r'def\s+\w+', content)) + 
                len(re.findall(r'class\s+\w+', content)) +
                len(re.findall(r'if\s+', content)) // 5
            ))
            
            return FileAnalysis(
                file_type="Python",
                content_summary=f"Python file with {len(key_components)} imports and {complexity_score} complexity",
                key_components=key_components,
                technologies=technologies,
                complexity_score=complexity_score,
                lines_of_code=lines_of_code
            )
        except Exception as e:
            self.logger.error(f"Error analyzing Python file {file_path}: {e}")
            return FileAnalysis(
                file_type="Python",
                content_summary="Error reading file",
                key_components=[],
                technologies=[],
                complexity_score=1,
                lines_of_code=0
            )
    
    def extract_technologies(self, content: str) -> List[str]:
        technologies = []
        
        # Common Python frameworks and libraries
        tech_patterns = {
            'Flask': r'from flask|import flask',
            'Django': r'from django|import django',
            'FastAPI': r'from fastapi|import fastapi',
            'Pandas': r'import pandas|from pandas',
            'NumPy': r'import numpy|from numpy',
            'Matplotlib': r'import matplotlib|from matplotlib',
            'Requests': r'import requests|from requests',
            'SQLAlchemy': r'from sqlalchemy|import sqlalchemy',
            'Pytest': r'import pytest|from pytest',
            'Ollama': r'import ollama|from ollama',
            'GitPython': r'import git|from git',
            'Aiohttp': r'import aiohttp|from aiohttp',
            'Httpx': r'import httpx|from httpx',
            'PyPDF2': r'import PyPDF2|from PyPDF2',
            'Click': r'import click|from click',
            'Rich': r'import rich|from rich',
            'PyYAML': r'import yaml|from yaml',
            'Python-dotenv': r'from dotenv|import dotenv',
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                technologies.append(tech)
        
        return technologies

class JavaScriptFileHandler(FileHandler):
    """Handler for JavaScript/TypeScript files"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
            
            # Extract imports
            imports = re.findall(r'import\s+(?:.*?from\s+)?[\'"]([^\'"]+)[\'"]', content)
            key_components = [imp.split('/')[-1].split('.')[0] for imp in imports]
            
            technologies = self.extract_technologies(content)
            
            # Complexity scoring
            complexity_score = min(10, max(1,
                len(re.findall(r'function\s+\w+', content)) +
                len(re.findall(r'const\s+\w+\s*=', content)) // 3 +
                len(re.findall(r'if\s*\(', content)) // 2
            ))
            
            return FileAnalysis(
                file_type="JavaScript/TypeScript",
                content_summary=f"JS/TS file with {len(key_components)} imports and {complexity_score} complexity",
                key_components=key_components,
                technologies=technologies,
                complexity_score=complexity_score,
                lines_of_code=lines_of_code
            )
        except Exception as e:
            self.logger.error(f"Error analyzing JS/TS file {file_path}: {e}")
            return FileAnalysis(
                file_type="JavaScript/TypeScript",
                content_summary="Error reading file",
                key_components=[],
                technologies=[],
                complexity_score=1,
                lines_of_code=0
            )
    
    def extract_technologies(self, content: str) -> List[str]:
        technologies = []
        
        tech_patterns = {
            'React': r'import.*react|from.*react',
            'Vue': r'import.*vue|from.*vue',
            'Angular': r'import.*angular|from.*angular',
            'Node.js': r'require\(|import.*node',
            'Express': r'express|app\.(get|post|put|delete)',
            'TypeScript': r'interface|type\s+\w+|:\s*\w+',
            'Next.js': r'next|pages/|app/',
            'Vite': r'vite|import\.meta\.env',
            'Webpack': r'webpack|module\.exports',
            'Jest': r'jest|describe\(|test\(',
            'Cypress': r'cypress|cy\.',
            'Tailwind': r'tailwind|@apply',
            'Bootstrap': r'bootstrap|@media',
            'Axios': r'import.*axios|from.*axios',
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                technologies.append(tech)
        
        return technologies

class PackageJsonHandler(FileHandler):
    """Handler for package.json files"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.name == 'package.json'
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = list(data.get('dependencies', {}).keys())
            dev_dependencies = list(data.get('devDependencies', {}).keys())
            scripts = list(data.get('scripts', {}).keys())
            
            all_deps = dependencies + dev_dependencies
            technologies = self.extract_technologies(all_deps)
            
            return FileAnalysis(
                file_type="Package.json",
                content_summary=f"Node.js project with {len(dependencies)} dependencies and {len(scripts)} scripts",
                key_components=scripts,
                technologies=technologies,
                complexity_score=min(10, len(all_deps) // 5 + 1),
                lines_of_code=len(str(data).split('\n'))
            )
        except Exception as e:
            self.logger.error(f"Error analyzing package.json {file_path}: {e}")
            return FileAnalysis(
                file_type="Package.json",
                content_summary="Error reading package.json",
                key_components=[],
                technologies=[],
                complexity_score=1,
                lines_of_code=0
            )
    
    def extract_technologies(self, dependencies: List[str]) -> List[str]:
        technologies = []
        
        tech_mapping = {
            'react': 'React',
            'vue': 'Vue.js',
            'angular': 'Angular',
            'express': 'Express.js',
            'next': 'Next.js',
            'vite': 'Vite',
            'webpack': 'Webpack',
            'jest': 'Jest',
            'cypress': 'Cypress',
            'tailwindcss': 'Tailwind CSS',
            'bootstrap': 'Bootstrap',
            'typescript': 'TypeScript',
            'eslint': 'ESLint',
            'prettier': 'Prettier',
            'nodemon': 'Nodemon',
            'axios': 'Axios',
            'lodash': 'Lodash',
            'moment': 'Moment.js',
            'dayjs': 'Day.js',
        }
        
        for dep in dependencies:
            dep_lower = dep.lower()
            for pattern, tech in tech_mapping.items():
                if pattern in dep_lower:
                    technologies.append(tech)
                    break
        
        return list(set(technologies))

class RequirementsTxtHandler(FileHandler):
    """Handler for requirements.txt files"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.name == 'requirements.txt'
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            dependencies = [line.strip().split('>=')[0].split('==')[0].split('<=')[0] 
                          for line in lines if line.strip() and not line.startswith('#')]
            
            technologies = self.extract_technologies(dependencies)
            
            return FileAnalysis(
                file_type="Requirements.txt",
                content_summary=f"Python project with {len(dependencies)} dependencies",
                key_components=dependencies,
                technologies=technologies,
                complexity_score=min(10, len(dependencies) // 3 + 1),
                lines_of_code=len(lines)
            )
        except Exception as e:
            self.logger.error(f"Error analyzing requirements.txt {file_path}: {e}")
            return FileAnalysis(
                file_type="Requirements.txt",
                content_summary="Error reading requirements.txt",
                key_components=[],
                technologies=[],
                complexity_score=1,
                lines_of_code=0
            )
    
    def extract_technologies(self, dependencies: List[str]) -> List[str]:
        technologies = []
        
        tech_mapping = {
            'flask': 'Flask',
            'django': 'Django',
            'fastapi': 'FastAPI',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'matplotlib': 'Matplotlib',
            'seaborn': 'Seaborn',
            'requests': 'Requests',
            'sqlalchemy': 'SQLAlchemy',
            'pytest': 'Pytest',
            'ollama': 'Ollama',
            'gitpython': 'GitPython',
            'aiohttp': 'Aiohttp',
            'httpx': 'Httpx',
            'pypdf2': 'PyPDF2',
            'click': 'Click',
            'rich': 'Rich',
            'pyyaml': 'PyYAML',
            'python-dotenv': 'Python-dotenv',
            'black': 'Black',
            'isort': 'isort',
            'mypy': 'MyPy',
            'pylint': 'Pylint',
            'celery': 'Celery',
            'redis': 'Redis',
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',
            'sqlite': 'SQLite',
        }
        
        for dep in dependencies:
            dep_lower = dep.lower()
            for pattern, tech in tech_mapping.items():
                if pattern in dep_lower:
                    technologies.append(tech)
                    break
        
        return list(set(technologies))

class ReadmeHandler(FileHandler):
    """Handler for README files"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.name.lower() in ['readme.md', 'readme.txt', 'readme']
    
    def analyze(self, file_path: Path) -> FileAnalysis:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            lines_of_code = len(lines)
            
            # Extract sections
            sections = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            
            # Extract code blocks
            code_blocks = re.findall(r'```(\w+)', content)
            
            technologies = self.extract_technologies(content)
            
            return FileAnalysis(
                file_type="README",
                content_summary=f"README with {len(sections)} sections and {len(code_blocks)} code examples",
                key_components=sections,
                technologies=technologies,
                complexity_score=min(10, len(sections) + len(code_blocks) // 2),
                lines_of_code=lines_of_code
            )
        except Exception as e:
            self.logger.error(f"Error analyzing README {file_path}: {e}")
            return FileAnalysis(
                file_type="README",
                content_summary="Error reading README",
                key_components=[],
                technologies=[],
                complexity_score=1,
                lines_of_code=0
            )
    
    def extract_technologies(self, content: str) -> List[str]:
        technologies = []
        
        # Look for technology mentions in README
        tech_patterns = {
            'Python': r'\bpython\b',
            'JavaScript': r'\bjavascript\b|\bjs\b',
            'TypeScript': r'\btypescript\b|\bts\b',
            'React': r'\breact\b',
            'Vue': r'\bvue\b',
            'Angular': r'\bangular\b',
            'Node.js': r'\bnode\.?js\b|\bnode\b',
            'Express': r'\bexpress\b',
            'Django': r'\bdjango\b',
            'Flask': r'\bflask\b',
            'FastAPI': r'\bfastapi\b',
            'Docker': r'\bdocker\b',
            'Kubernetes': r'\bkubernetes\b|\bk8s\b',
            'AWS': r'\baws\b|\bamazon\b',
            'Azure': r'\bazure\b',
            'GCP': r'\bgcp\b|\bgoogle cloud\b',
            'Git': r'\bgit\b',
            'GitHub': r'\bgithub\b',
            'GitLab': r'\bgitlab\b',
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                technologies.append(tech)
        
        return list(set(technologies))

class FileAnalyzer:
    """Main file analyzer that uses multiple handlers"""
    
    def __init__(self):
        self.handlers = [
            PythonFileHandler(),
            JavaScriptFileHandler(),
            PackageJsonHandler(),
            RequirementsTxtHandler(),
            ReadmeHandler(),
        ]
        self.logger = logging.getLogger(__name__)
    
    def analyze_file(self, file_path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file using appropriate handler"""
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler.analyze(file_path)
        
        self.logger.warning(f"No handler found for file: {file_path}")
        return None
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze all files in a project"""
        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        results = {
            'files_analyzed': 0,
            'total_lines': 0,
            'technologies': set(),
            'file_types': {},
            'complexity_score': 0,
            'analyses': []
        }
        
        # Priority files to analyze first
        priority_files = ['README.md', 'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml']
        
        for priority_file in priority_files:
            file_path = project_path / priority_file
            if file_path.exists():
                analysis = self.analyze_file(file_path)
                if analysis:
                    results['analyses'].append({
                        'file': str(file_path.relative_to(project_path)),
                        'analysis': analysis
                    })
                    results['files_analyzed'] += 1
                    results['total_lines'] += analysis.lines_of_code
                    results['technologies'].update(analysis.technologies)
                    results['complexity_score'] += analysis.complexity_score
        
        # Analyze code files
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.cpp', '.c'}
        exclude_patterns = {'node_modules', 'build', 'dist', '__pycache__', '.git', 'venv', '.env'}
        
        for file_path in project_path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in code_extensions and
                not any(pattern in str(file_path) for pattern in exclude_patterns)):
                
                analysis = self.analyze_file(file_path)
                if analysis:
                    results['analyses'].append({
                        'file': str(file_path.relative_to(project_path)),
                        'analysis': analysis
                    })
                    results['files_analyzed'] += 1
                    results['total_lines'] += analysis.lines_of_code
                    results['technologies'].update(analysis.technologies)
                    results['complexity_score'] += analysis.complexity_score
        
        # Convert set to list for JSON serialization
        results['technologies'] = list(results['technologies'])
        results['complexity_score'] = min(10, results['complexity_score'] // max(1, results['files_analyzed'] // 5))
        
        return results 