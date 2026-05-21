"""
Swarm Engine — File Templates

Generates deterministic scaffold files from templates.
No LLM, no Forge. Just string substitution with project config values.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_template(template: str, variables: dict[str, str]) -> str:
    """Simple {{variable}} substitution."""
    result = template
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", value)
    return result


# ---------------------------------------------------------------------------
# React SPA templates
# ---------------------------------------------------------------------------

PACKAGE_JSON = """{
  "name": "{{slug}}",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port {{port}} --host 127.0.0.1",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
"""

VITE_CONFIG = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: {{port}},
    host: '127.0.0.1',
  },
});
"""

TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "outDir": "dist"
  },
  "include": ["src"]
}
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{title}}</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
"""

MAIN_TSX = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

REACT_SPA_TEMPLATES: dict[str, str] = {
    "package.json": PACKAGE_JSON,
    "vite.config.ts": VITE_CONFIG,
    "tsconfig.json": TSCONFIG,
    "index.html": INDEX_HTML,
    "src/main.tsx": MAIN_TSX,
}


def write_scaffold_files(
    deliverable_root: Path,
    templates: dict[str, str],
    variables: dict[str, str],
) -> list[str]:
    """
    Write scaffold files from templates. Returns list of files written.
    No LLM. Deterministic. Guaranteed correct.
    """
    written = []
    for rel_path, template in templates.items():
        content = render_template(template, variables)
        full_path = deliverable_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        written.append(rel_path)
    return written
