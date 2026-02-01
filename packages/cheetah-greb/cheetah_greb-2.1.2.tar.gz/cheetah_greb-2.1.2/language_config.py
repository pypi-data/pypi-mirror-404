"""
Language configuration and support utilities for SWE-grep.
"""

import os
from typing import Dict, List, Optional, Set
from pathlib import Path


class LanguageConfig:
    """Centralized language configuration management."""

    def __init__(self):
        self.enabled_languages = self._load_enabled_languages()
        self.enabled_frameworks = self._load_enabled_frameworks()

    def _load_enabled_languages(self) -> Set[str]:
        """Load enabled languages from environment variables."""
        languages = [
            'python', 'javascript', 'typescript', 'java', 'go', 'rust',
            'cpp', 'csharp', 'php', 'ruby', 'swift', 'kotlin', 'scala',
            'dart', 'lua', 'r', 'perl', 'shell', 'sql'
        ]

        enabled = set()
        for lang in languages:
            env_var = f'ENABLE_{lang.upper()}_SUPPORT'
            if os.getenv(env_var, 'true').lower() == 'true':
                enabled.add(lang)

        return enabled

    def _load_enabled_frameworks(self) -> Set[str]:
        """Load enabled frameworks from environment variables."""
        frameworks = [
            'react', 'vue', 'angular', 'django', 'flask', 'rails',
            'spring', 'express', 'next', 'nuxt'
        ]

        enabled = set()
        for framework in frameworks:
            env_var = f'ENABLE_{framework.upper()}_PATTERNS'
            if os.getenv(env_var, 'true').lower() == 'true':
                enabled.add(framework)

        return enabled

    def is_language_enabled(self, language: str) -> bool:
        """Check if a language is enabled."""
        return language.lower() in self.enabled_languages

    def is_framework_enabled(self, framework: str) -> bool:
        """Check if a framework is enabled."""
        return framework.lower() in self.enabled_frameworks

    def get_file_patterns_for_language(self, language: str) -> List[str]:
        """Get file patterns for a specific language."""
        if not self.is_language_enabled(language):
            return []

        # This would integrate with the glob tool patterns
        patterns = {
            'python': ['*.py', 'requirements*.txt', 'pyproject.toml', 'setup.py'],
            'javascript': ['*.js', '*.jsx', '*.mjs', '*.cjs', 'package.json'],
            'typescript': ['*.ts', '*.tsx', '*.d.ts', 'tsconfig.json'],
            'java': ['*.java', '*.class', '*.jar', 'pom.xml', 'build.gradle'],
            'go': ['*.go', 'go.mod', 'go.sum'],
            'rust': ['*.rs', 'Cargo.toml', 'Cargo.lock'],
            'cpp': ['*.cpp', '*.cxx', '*.cc', '*.c', '*.h', '*.hpp'],
            'csharp': ['*.cs', '*.csx', '*.csproj', '*.sln'],
            'php': ['*.php', '*.phtml', 'composer.json'],
            'ruby': ['*.rb', 'Gemfile', 'Rakefile'],
            'swift': ['*.swift', 'Package.swift'],
            'kotlin': ['*.kt', '*.kts', 'build.gradle'],
            'scala': ['*.scala', '*.sc', 'build.sbt'],
            'dart': ['*.dart', 'pubspec.yaml'],
            'lua': ['*.lua'],
            'r': ['*.r', '*.R'],
            'perl': ['*.pl', '*.pm'],
            'shell': ['*.sh', '*.bash', '*.zsh'],
            'sql': ['*.sql'],
        }

        return patterns.get(language.lower(), [])

    def get_framework_patterns(self, framework: str) -> List[str]:
        """Get patterns for a specific framework."""
        if not self.is_framework_enabled(framework):
            return []

        patterns = {
            'react': ['*.jsx', '*.tsx', 'src/components/**', 'src/hooks/**'],
            'vue': ['*.vue', 'src/components/**', 'src/views/**'],
            'angular': ['*.ts', '*.html', 'src/app/**'],
            'django': ['*.py', 'settings.py', 'urls.py', 'templates/**'],
            'flask': ['*.py', 'app.py', 'templates/**'],
            'rails': ['*.rb', 'config/routes.rb', 'app/**'],
            'spring': ['*.java', 'application*.yml', 'src/main/**'],
            'express': ['*.js', 'app.js', 'routes/**'],
            'next': ['*.js', '*.jsx', 'pages/**', 'components/**'],
            'nuxt': ['*.js', '*.vue', 'pages/**'],
        }

        return patterns.get(framework.lower(), [])

    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect language from file path."""
        path = Path(file_path)
        extension = path.suffix.lower()

        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.scala': 'scala',
            '.dart': 'dart',
            '.lua': 'lua',
            '.r': 'r',
            '.pl': 'perl',
            '.pm': 'perl',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.sql': 'sql',
        }

        detected = extension_map.get(extension)
        return detected if detected and self.is_language_enabled(detected) else None

    def get_search_enhancements(self, language: str, query: str) -> List[str]:
        """Get language-specific search enhancements."""
        if not self.is_language_enabled(language):
            return []

        enhancements = {
            'python': {
                'auth': ['def', 'class', 'decorator', 'authenticate', 'login', 'permission'],
                'database': ['db', 'session', 'connection', 'query', 'orm'],
                'api': ['api', 'route', 'view', 'request', 'response', 'json'],
                'error': ['error', 'exception', 'try', 'except', 'raise'],
            },
            'javascript': {
                'auth': ['auth', 'login', 'jwt', 'token', 'session', 'cookie'],
                'database': ['db', 'database', 'mongoose', 'sequelize', 'query'],
                'api': ['api', 'endpoint', 'route', 'express', 'req', 'res'],
                'error': ['error', 'catch', 'throw', 'try', 'promise'],
            },
            'typescript': {
                'auth': ['auth', 'login', 'jwt', 'token', 'interface', 'type'],
                'database': ['db', 'database', 'prisma', 'typeorm', 'model'],
                'api': ['api', 'controller', 'service', 'dto', 'request'],
                'error': ['error', 'exception', 'catch', 'throw', 'Error'],
            },
            'java': {
                'auth': ['auth', 'login', 'spring', 'security', 'jwt', 'token'],
                'database': ['db', 'jpa', 'hibernate', 'repository', 'entity'],
                'api': ['api', 'controller', 'service', 'repository', '@RestController'],
                'error': ['error', 'exception', 'try', 'catch', 'throw'],
            },
            'go': {
                'auth': ['auth', 'login', 'jwt', 'token', 'middleware'],
                'database': ['db', 'gorm', 'sql', 'query', 'connection'],
                'api': ['api', 'handler', 'router', 'http', 'request', 'response'],
                'error': ['error', 'err', 'panic', 'recover'],
            },
            'rust': {
                'auth': ['auth', 'login', 'jwt', 'token'],
                'database': ['db', 'diesel', 'sqlx', 'query', 'connection'],
                'api': ['api', 'handler', 'router', 'http', 'request', 'response'],
                'error': ['error', 'result', 'option', 'panic'],
            },
        }

        query_lower = query.lower()
        language_enhancements = enhancements.get(language.lower(), {})

        for concept, keywords in language_enhancements.items():
            if concept in query_lower:
                return [kw for kw in keywords if kw not in query_lower]

        return []


# Global language configuration instance
language_config = LanguageConfig()