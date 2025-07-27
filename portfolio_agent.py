#!/usr/bin/env python3
"""
Portfolio Agent - AI-powered GitHub Pages portfolio and resume manager
"""

import os
import sys
import json
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import re

try:
    import ollama
    import git
except ImportError:
    print("Dependencies not found. Please run setup again.")
    sys.exit(1)

@dataclass
class ProjectInfo:
    name: str
    path: str
    description: str
    technologies: List[str]
    bullet_points: List[str]
    special_features: List[str]

@dataclass
class Config:
    portfolio_path: str
    git_user_name: str
    git_user_email: str
    ollama_model: str = "llama3.1:8b"

class PortfolioAgent:
    def __init__(self, config_path: str = "~/.portfolio_agent/config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load_config()
        self.logger = self.setup_logging()
        self.ollama_client = None
    
    def setup_logging(self):
        log_dir = self.config_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"agent_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def load_config(self):
        if not self.config_path.exists():
            return self.setup_config()
        
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)
        return Config(**config_data)
    
    def setup_config(self):
        print("🚀 Portfolio Agent - First Time Setup")
        print("=" * 50)
        
        portfolio_path = input("Enter path to your portfolio folder: ").strip()
        if portfolio_path.startswith("~"):
            portfolio_path = str(Path(portfolio_path).expanduser())
        
        # Validate path
        portfolio_path_obj = Path(portfolio_path)
        if not portfolio_path_obj.exists():
            print(f"❌ Portfolio path does not exist: {portfolio_path}")
            sys.exit(1)
        
        required_files = ["src/Portfolio.tsx", "public/resume.html", "package.json"]
        for req_file in required_files:
            if not (portfolio_path_obj / req_file).exists():
                print(f"❌ Required file not found: {req_file}")
                sys.exit(1)
        
        git_user_name = input("Enter your Git username: ").strip()
        git_user_email = input("Enter your Git email: ").strip()
        
        config = Config(
            portfolio_path=portfolio_path,
            git_user_name=git_user_name,
            git_user_email=git_user_email
        )
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config.__dict__, f, indent=2)
        
        print("✅ Configuration saved!")
        return config
    
    async def initialize_ollama(self):
        try:
            self.ollama_client = ollama.AsyncClient()
            models = await self.ollama_client.list()
            model_names = [model.get('name', '') for model in models.get('models', [])]
            
            if self.config.ollama_model not in model_names:
                print(f"📥 Downloading {self.config.ollama_model}...")
                await self.ollama_client.pull(self.config.ollama_model)
        except Exception as e:
            self.logger.error(f"Ollama initialization failed: {e}")
            raise
    
    async def analyze_project(self, project_path: str):
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        self.logger.info(f"Analyzing project: {project_path}")
        
        # Read key files
        file_contents = {}
        priority_files = ["README.md", "package.json", "requirements.txt", "setup.py"]
        
        for file_name in priority_files:
            file_path = project_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) < 5000:
                            file_contents[file_name] = content
                        else:
                            file_contents[file_name] = content[:5000] + "... (truncated)"
                except Exception as e:
                    self.logger.warning(f"Could not read {file_name}: {e}")
        
        # Scan code files
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs'}
        exclude_patterns = {'node_modules', 'build', 'dist', '__pycache__', '.git', 'venv'}
        
        code_files = []
        for file_path in project_path.rglob('*'):
            if (file_path.suffix in code_extensions and
                not any(pattern in str(file_path) for pattern in exclude_patterns)):
                code_files.append(file_path)
        
        # Read sample files
        for code_file in code_files[:5]:
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 1500:
                        file_contents[str(code_file.relative_to(project_path))] = content
            except Exception as e:
                self.logger.warning(f"Could not read {code_file}: {e}")
        
        return await self._generate_project_analysis(project_path.name, file_contents)
    
    async def _generate_project_analysis(self, project_name: str, file_contents: Dict[str, str]):
        context = f"Project Name: {project_name}\n\n"
        for filename, content in file_contents.items():
            context += f"=== {filename} ===\n{content}\n\n"
        
        prompt = f"""
Analyze this software project and provide detailed, accurate information based on the actual code and documentation.

Project files:
{context}

IMPORTANT: Read the README.md, requirements.txt, package.json, and main code files carefully to extract:
- What the project actually does (not generic descriptions)
- All technologies and frameworks used
- Key features and capabilities
- Technical achievements

CRITICAL: You must respond ONLY with valid JSON. Do not include any text before or after the JSON.

Respond with ONLY this JSON format:
{{
    "description": "Detailed description of what this project does based on README and code",
    "technologies": ["tech1", "tech2", "tech3"],
    "bullet_points": [
        "Specific technical feature 1",
        "Specific technical feature 2", 
        "Specific technical feature 3"
    ],
    "special_features": [
        "Unique technical aspect 1",
        "Unique technical aspect 2"
    ]
}}

Focus on:
- Real functionality from README.md
- Technologies from requirements.txt, package.json, imports
- Specific features mentioned in code
- Technical complexity and achievements
- Avoid generic descriptions like "modern development practices"

Remember: Respond with ONLY the JSON object, no other text.
"""
        
        try:
            response = await self.ollama_client.chat(
                model=self.config.ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response['message']['content']
            self.logger.info(f"AI Response: {response_text}")
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    if all(key in analysis for key in ["description", "technologies", "bullet_points", "special_features"]):
                        project_info = ProjectInfo(
                            name=project_name,
                            path="",
                            description=analysis["description"],
                            technologies=analysis["technologies"],
                            bullet_points=analysis["bullet_points"],
                            special_features=analysis["special_features"]
                        )
                        return project_info
                    else:
                        self.logger.error(f"Missing required fields in AI response: {analysis}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing failed: {e}")
                    self.logger.error(f"Attempted to parse: {json_match.group()}")
            else:
                self.logger.error("No JSON found in AI response")
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
        
        # Fallback
        return ProjectInfo(
            name=project_name,
            path="",
            description=f"A software project implementing {project_name}",
            technologies=self._detect_technologies(file_contents),
            bullet_points=[
                f"Built {project_name} with modern development practices",
                "Features clean, maintainable code architecture",
                "Demonstrates technical problem-solving skills"
            ],
            special_features=["Custom implementation", "User-friendly interface"]
        )
    
    def _detect_technologies(self, file_contents: Dict[str, str]):
        technologies = []
        for filename, content in file_contents.items():
            if filename.endswith('.py'):
                technologies.append('Python')
            elif filename.endswith(('.js', '.jsx')):
                technologies.append('JavaScript')
            elif filename.endswith(('.ts', '.tsx')):
                technologies.append('TypeScript')
            elif filename == 'package.json':
                if 'react' in content.lower():
                    technologies.append('React')
                if 'next' in content.lower():
                    technologies.append('Next.js')
                if 'tailwind' in content.lower():
                    technologies.append('Tailwind CSS')
                if 'typescript' in content.lower():
                    technologies.append('TypeScript')
            elif filename == 'requirements.txt':
                # Parse Python dependencies
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                        if package.lower() in ['flask', 'fastapi', 'django', 'streamlit']:
                            technologies.append(package.title())
                        elif package.lower() in ['opencv-python', 'cv2']:
                            technologies.append('OpenCV')
                        elif package.lower() in ['torch', 'pytorch']:
                            technologies.append('PyTorch')
                        elif package.lower() in ['tensorflow', 'tf']:
                            technologies.append('TensorFlow')
                        elif package.lower() in ['transformers', 'huggingface']:
                            technologies.append('Hugging Face')
                        elif package.lower() in ['mlflow']:
                            technologies.append('MLflow')
                        elif package.lower() in ['yolo', 'ultralytics']:
                            technologies.append('YOLO')
                        elif package.lower() in ['pandas']:
                            technologies.append('Pandas')
                        elif package.lower() in ['numpy']:
                            technologies.append('NumPy')
                        elif package.lower() in ['scikit-learn', 'sklearn']:
                            technologies.append('Scikit-learn')
                        elif package.lower() in ['matplotlib']:
                            technologies.append('Matplotlib')
                        elif package.lower() in ['seaborn']:
                            technologies.append('Seaborn')
                        elif package.lower() in ['plotly']:
                            technologies.append('Plotly')
                        elif package.lower() in ['requests']:
                            technologies.append('Requests')
                        elif package.lower() in ['beautifulsoup4', 'bs4']:
                            technologies.append('BeautifulSoup')
                        elif package.lower() in ['selenium']:
                            technologies.append('Selenium')
                        elif package.lower() in ['pytest']:
                            technologies.append('Pytest')
                        elif package.lower() in ['jupyter']:
                            technologies.append('Jupyter')
                        elif package.lower() in ['streamlit']:
                            technologies.append('Streamlit')
                        elif package.lower() in ['gradio']:
                            technologies.append('Gradio')
                        elif package.lower() in ['docker']:
                            technologies.append('Docker')
                        elif package.lower() in ['kubernetes']:
                            technologies.append('Kubernetes')
                        elif package.lower() in ['redis']:
                            technologies.append('Redis')
                        elif package.lower() in ['postgresql', 'psycopg2']:
                            technologies.append('PostgreSQL')
                        elif package.lower() in ['mysql', 'mysql-connector']:
                            technologies.append('MySQL')
                        elif package.lower() in ['mongodb', 'pymongo']:
                            technologies.append('MongoDB')
                        elif package.lower() in ['sqlalchemy']:
                            technologies.append('SQLAlchemy')
                        elif package.lower() in ['alembic']:
                            technologies.append('Alembic')
                        elif package.lower() in ['celery']:
                            technologies.append('Celery')
                        elif package.lower() in ['airflow']:
                            technologies.append('Apache Airflow')
                        elif package.lower() in ['kafka']:
                            technologies.append('Apache Kafka')
                        elif package.lower() in ['elasticsearch']:
                            technologies.append('Elasticsearch')
                        elif package.lower() in ['opencv-python']:
                            technologies.append('OpenCV')
                        elif package.lower() in ['pillow', 'pil']:
                            technologies.append('Pillow')
                        elif package.lower() in ['tesseract']:
                            technologies.append('Tesseract OCR')
                        elif package.lower() in ['pytesseract']:
                            technologies.append('Tesseract OCR')
                        elif package.lower() in ['pdf2image']:
                            technologies.append('PDF Processing')
                        elif package.lower() in ['pypdf2', 'pypdf']:
                            technologies.append('PDF Processing')
                        elif package.lower() in ['reportlab']:
                            technologies.append('ReportLab')
                        elif package.lower() in ['jinja2']:
                            technologies.append('Jinja2')
                        elif package.lower() in ['flask-cors']:
                            technologies.append('Flask-CORS')
                        elif package.lower() in ['flask-sqlalchemy']:
                            technologies.append('Flask-SQLAlchemy')
                        elif package.lower() in ['flask-migrate']:
                            technologies.append('Flask-Migrate')
                        elif package.lower() in ['flask-login']:
                            technologies.append('Flask-Login')
                        elif package.lower() in ['flask-wtf']:
                            technologies.append('Flask-WTF')
                        elif package.lower() in ['flask-restful']:
                            technologies.append('Flask-RESTful')
                        elif package.lower() in ['flask-socketio']:
                            technologies.append('Flask-SocketIO')
                        elif package.lower() in ['flask-mail']:
                            technologies.append('Flask-Mail')
                        elif package.lower() in ['flask-bcrypt']:
                            technologies.append('Flask-Bcrypt')
                        elif package.lower() in ['flask-jwt-extended']:
                            technologies.append('Flask-JWT')
                        elif package.lower() in ['flask-limiter']:
                            technologies.append('Flask-Limiter')
                        elif package.lower() in ['flask-caching']:
                            technologies.append('Flask-Caching')
                        elif package.lower() in ['flask-compress']:
                            technologies.append('Flask-Compress')
                        elif package.lower() in ['flask-talisman']:
                            technologies.append('Flask-Talisman')
                        elif package.lower() in ['flask-helmet']:
                            technologies.append('Flask-Helmet')
                        elif package.lower() in ['flask-cors']:
                            technologies.append('Flask-CORS')
                        elif package.lower() in ['flask-sqlalchemy']:
                            technologies.append('Flask-SQLAlchemy')
                        elif package.lower() in ['flask-migrate']:
                            technologies.append('Flask-Migrate')
                        elif package.lower() in ['flask-login']:
                            technologies.append('Flask-Login')
                        elif package.lower() in ['flask-wtf']:
                            technologies.append('Flask-WTF')
                        elif package.lower() in ['flask-restful']:
                            technologies.append('Flask-RESTful')
                        elif package.lower() in ['flask-socketio']:
                            technologies.append('Flask-SocketIO')
                        elif package.lower() in ['flask-mail']:
                            technologies.append('Flask-Mail')
                        elif package.lower() in ['flask-bcrypt']:
                            technologies.append('Flask-Bcrypt')
                        elif package.lower() in ['flask-jwt-extended']:
                            technologies.append('Flask-JWT')
                        elif package.lower() in ['flask-limiter']:
                            technologies.append('Flask-Limiter')
                        elif package.lower() in ['flask-caching']:
                            technologies.append('Flask-Caching')
                        elif package.lower() in ['flask-compress']:
                            technologies.append('Flask-Compress')
                        elif package.lower() in ['flask-talisman']:
                            technologies.append('Flask-Talisman')
                        elif package.lower() in ['flask-helmet']:
                            technologies.append('Flask-Helmet')
        return list(set(technologies))
    
    def check_project_exists(self, project_name: str) -> bool:
        """Check if a project already exists in the portfolio"""
        portfolio_file = Path(self.config.portfolio_path) / "src" / "Portfolio.tsx"
        
        try:
            with open(portfolio_file, 'r') as f:
                content = f.read()
            
            # Check if project title exists in the projects array
            # Look for the project name in title field
            import re
            project_pattern = rf"title:\s*['\"]([^'\"]*{re.escape(project_name)}[^'\"]*)['\"]"
            matches = re.findall(project_pattern, content, re.IGNORECASE)
            
            if matches:
                self.logger.info(f"Project '{project_name}' already exists in portfolio")
                return True
            
            # Also check for similar names (case-insensitive)
            title_pattern = r"title:\s*['\"]([^'\"]*)['\"]"
            all_titles = re.findall(title_pattern, content)
            
            for title in all_titles:
                if project_name.lower() in title.lower() or title.lower() in project_name.lower():
                    self.logger.info(f"Similar project '{title}' already exists in portfolio")
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking if project exists: {e}")
            return False

    def update_portfolio(self, project_info: ProjectInfo):
        portfolio_file = Path(self.config.portfolio_path) / "src" / "Portfolio.tsx"
        
        try:
            with open(portfolio_file, 'r') as f:
                content = f.read()
            
            new_project = self._generate_portfolio_entry(project_info)
            
            # Insert at beginning of projects array
            if "const projects = [" in content:
                insertion_point = content.find("const projects = [") + len("const projects = [")
                # Find the first opening brace after the array declaration
                brace_pos = content.find("[", insertion_point)
                if brace_pos != -1:
                    insertion_point = brace_pos + 1
                
                updated_content = (
                    content[:insertion_point] +
                    f"\n    {new_project}," +
                    content[insertion_point:]
                )
                
                with open(portfolio_file, 'w') as f:
                    f.write(updated_content)
                
                self.logger.info("Portfolio updated")
                return True
            else:
                self.logger.error("Could not find 'const projects = [' in portfolio file")
                return False
        except Exception as e:
            self.logger.error(f"Portfolio update failed: {e}")
        return False
    
    def _generate_portfolio_entry(self, project_info: ProjectInfo):
        title = project_info.name.replace('"', '\\"')
        description = project_info.description.replace('"', '\\"')
        tech = ', '.join(f"'{tech}'" for tech in project_info.technologies)
        highlights = ',\n      '.join(f"'{h}'" for h in project_info.bullet_points)
        
        return f'''{{
      title: '{title}',
      tech: [{tech}],
      description: '{description}',
      highlights: [{highlights}]
    }}'''
    
    async def update_resume(self, project_info: ProjectInfo, mode: str = "interactive"):
        resume_file = Path(self.config.portfolio_path) / "public" / "resume.html"
        
        if mode != "auto":
            add_to_resume = input(f"\n📄 Add '{project_info.name}' to resume? (y/n): ").lower() == 'y'
            if not add_to_resume:
                return True
        
        # Show current resume projects if in interactive mode
        if mode == "interactive":
            current_projects = self._get_current_resume_projects(resume_file)
            if current_projects:
                print(f"\n📋 Current resume projects:")
                for i, project in enumerate(current_projects, 1):
                    print(f"  {i}. {project}")
                
                if len(current_projects) >= 3:
                    print(f"\n⚠️  Resume has 3 projects. Which one to replace?")
                    print("  0. Don't add to resume")
                    try:
                        choice = int(input("  Enter number (0-3): "))
                        if choice == 0:
                            print("⏭️  Skipping resume update")
                            return True
                        elif 1 <= choice <= 3:
                            print(f"✅ Will replace project {choice}")
                        else:
                            print("❌ Invalid choice, skipping resume update")
                            return True
                    except ValueError:
                        print("❌ Invalid input, skipping resume update")
                        return True
        
        # Generate resume bullets
        resume_bullets = await self._generate_resume_bullets(project_info)
        
        # Update resume HTML
        try:
            with open(resume_file, 'r') as f:
                content = f.read()
            
            # This is a simplified update - you'll need to adapt based on your HTML structure
            self.logger.info("Resume update would happen here - customize based on your HTML")
            
            # Generate PDF
            result = subprocess.run(
                ["npm", "run", "generate-pdf"],
                cwd=self.config.portfolio_path,
                capture_output=True
            )
            
            if result.returncode == 0:
                print("📄 PDF generated successfully")
                return True
        except Exception as e:
            self.logger.error(f"Resume update failed: {e}")
        
        return False
    
    def _get_current_resume_projects(self, resume_file: Path) -> List[str]:
        """Extract current projects from resume HTML"""
        try:
            with open(resume_file, 'r') as f:
                content = f.read()
            
            # Simple regex to find project names in resume
            # This is a basic implementation - you may need to customize based on your HTML structure
            import re
            project_matches = re.findall(r'<h[3-6][^>]*>([^<]+)</h[3-6]>', content)
            
            # Filter for likely project names (not section headers)
            projects = []
            for match in project_matches:
                if len(match.strip()) > 3 and not any(word in match.lower() for word in ['experience', 'education', 'skills', 'contact']):
                    projects.append(match.strip())
            
            return projects[:3]  # Return max 3 projects
        except Exception as e:
            self.logger.error(f"Error reading resume projects: {e}")
            return []
    
    async def _generate_resume_bullets(self, project_info: ProjectInfo):
        prompt = f"""
Generate 3 professional resume bullet points for:
Project: {project_info.name}
Description: {project_info.description}
Technologies: {', '.join(project_info.technologies)}

Requirements:
- Use action verbs (Built, Developed, Implemented)
- Include realistic metrics for a beginner developer
- ATS-optimized keywords
- Each bullet should be concise

Format as JSON: ["bullet 1", "bullet 2", "bullet 3"]
"""
        
        try:
            response = await self.ollama_client.chat(
                model=self.config.ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response['message']['content']
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                bullets = json.loads(json_match.group())
                return bullets[:3]
        except Exception as e:
            self.logger.error(f"Resume bullets generation failed: {e}")
        
        # Fallback
        return [
            f"Built {project_info.name} using {project_info.technologies[0] if project_info.technologies else 'modern technologies'}",
            f"Implemented key features with focus on user experience",
            "Demonstrated problem-solving and clean code practices"
        ]
    
    def git_workflow(self, commit_message: str = None):
        try:
            repo = git.Repo(self.config.portfolio_path)
            
            if not repo.is_dirty():
                print("📝 No changes to commit")
                return True
            
            if not commit_message:
                commit_message = f"Update portfolio - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Start local development server
            print("🌐 Starting local development server...")
            dev_server = subprocess.Popen(
                ["npm", "start"],
                cwd=self.config.portfolio_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment for server to start
            import time
            time.sleep(3)
            
            # Check if server started successfully
            if dev_server.poll() is None:
                print("✅ Local server started at http://localhost:3000")
                print("📱 Preview your changes in the browser")
                
                # Ask user if they want to deploy
                deploy_choice = input("\n🤔 Do you want to deploy these changes? (y/n): ").lower().strip()
                
                # Stop the development server
                print("🛑 Stopping local server...")
                dev_server.terminate()
                dev_server.wait()
                print("✅ Local server stopped")
                
                if deploy_choice == 'y':
                    print("🚀 Proceeding with deployment...")
                    
                    # Create backup branch before making changes
                    backup_branch_name = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    print(f"💾 Creating backup branch: {backup_branch_name}")
                    
                    # Ensure we're on main branch
                    if repo.active_branch.name != 'main':
                        repo.git.checkout('main')
                    
                    # Create and push backup branch
                    backup_branch = repo.create_head(backup_branch_name)
                    backup_branch.checkout()
                    repo.git.add(A=True)
                    repo.index.commit(f"Backup before: {commit_message}")
                    
                    # Push backup branch
                    origin = repo.remote(name='origin')
                    origin.push(backup_branch_name)
                    
                    # Switch back to main and apply changes
                    repo.git.checkout('main')
                    repo.git.add(A=True)
                    repo.index.commit(commit_message)
                    origin.push()
                    
                    print(f"✅ Backup created: {backup_branch_name}")
                    
                    # Deploy
                    print("🚀 Deploying to GitHub Pages...")
                    result = subprocess.run(
                        ["npm", "run", "deploy"],
                        cwd=self.config.portfolio_path,
                        capture_output=True
                    )
                    
                    if result.returncode == 0:
                        print("✅ Deployed successfully!")
                        return True
                    else:
                        self.logger.error(f"Deployment failed: {result.stderr}")
                        return False
                else:
                    print("⏭️ Rolling back changes...")
                    
                    # Revert all changes
                    repo.git.reset("--hard", "HEAD")
                    repo.git.clean("-fd")
                    
                    print("✅ Changes rolled back successfully")
                    return True
            else:
                # Server failed to start
                stdout, stderr = dev_server.communicate()
                self.logger.error(f"Failed to start local server: {stderr.decode()}")
                print("❌ Failed to start local server")
                return False
                
        except Exception as e:
            self.logger.error(f"Git workflow failed: {e}")
            return False
    
    async def run_workflow(self, project_path: str, mode: str = "interactive"):
        try:
            print(f"🔄 Starting Portfolio Agent workflow")
            print(f"📁 Project: {project_path}")
            print(f"📋 Mode: {mode}")
            print("=" * 50)
            
            # Initialize AI
            print("\n🤖 Initializing AI model...")
            await self.initialize_ollama()
            print("✅ AI model ready")
            
            # Analyze project
            print("\n1️⃣ Analyzing project...")
            project_info = await self.analyze_project(project_path)
            
            print(f"✅ Project analyzed: {project_info.name}")
            print(f"📝 Description: {project_info.description}")
            print(f"🔧 Technologies: {', '.join(project_info.technologies)}")
            print("\n📋 Key highlights:")
            for i, point in enumerate(project_info.bullet_points, 1):
                print(f"  {i}. {point}")
            
            if mode == "analyze-only":
                print("\n🔍 Analysis complete!")
                return True
            
            if mode == "dry-run":
                print("\n🔍 DRY RUN - No changes would be made")
                return True
            
            # Check if project already exists
            print("\n🔍 Checking if project already exists in portfolio...")
            if self.check_project_exists(project_info.name):
                print(f"⚠️  Project '{project_info.name}' already exists in portfolio!")
                print("⏭️  Workflow stopped to prevent duplicates")
                return False
            
            print("✅ Project is new - proceeding with integration")
            
            # Confirm in interactive mode
            if mode == "interactive":
                proceed = input(f"\n🤔 Add '{project_info.name}' to portfolio? (y/n): ").lower()
                if proceed != 'y':
                    print("⏭️  Operation cancelled")
                    return False
            
            # Update portfolio
            print("\n2️⃣ Updating portfolio...")
            if self.update_portfolio(project_info):
                print("✅ Portfolio.tsx updated")
            else:
                print("❌ Portfolio update failed")
                return False
            
            # Update resume
            print("\n3️⃣ Updating resume...")
            if await self.update_resume(project_info, mode):
                print("✅ Resume updated")
            else:
                print("❌ Resume update failed")
                return False
            
            # Git workflow with preview
            print("\n4️⃣ Preview and deploy changes...")
            commit_msg = f"Add {project_info.name} to portfolio"
            
            if self.git_workflow(commit_msg):
                print("✅ All changes deployed!")
                print(f"🌐 Portfolio updated with '{project_info.name}'")
            else:
                print("❌ Deployment failed")
                return False
            
            print("\n🎉 Workflow completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            print(f"❌ Workflow failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Portfolio Agent - AI-powered portfolio manager")
    parser.add_argument("project_path", help="Path to project folder")
    parser.add_argument("--mode", choices=["interactive", "auto", "dry-run", "analyze-only"],
                       default="interactive", help="Execution mode")
    parser.add_argument("--config", default="~/.portfolio_agent/config.json", help="Config file path")
    parser.add_argument("--version", action="version", version="Portfolio Agent 1.0.0")
    
    args = parser.parse_args()
    
    # Validate project path
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)
    
    try:
        agent = PortfolioAgent(args.config)
        success = asyncio.run(agent.run_workflow(str(project_path), args.mode))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
