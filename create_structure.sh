#!/bin/bash

# Create main directory structure
mkdir -p writers-room-x/api/app/{models,schemas,routers,services,agents,rag,metrics,utils,tests}
mkdir -p writers-room-x/ui
mkdir -p writers-room-x/{artifacts,data,configs,docker}

# Create empty __init__.py files
touch writers-room-x/api/app/__init__.py
touch writers-room-x/api/app/models/__init__.py
touch writers-room-x/api/app/schemas/__init__.py
touch writers-room-x/api/app/routers/__init__.py
touch writers-room-x/api/app/services/__init__.py
touch writers-room-x/api/app/agents/__init__.py
touch writers-room-x/api/app/rag/__init__.py
touch writers-room-x/api/app/metrics/__init__.py
touch writers-room-x/api/app/utils/__init__.py

# Create main app files
touch writers-room-x/api/app/{main.py,config.py,deps.py,db.py}

# Create config files
touch writers-room-x/configs/{agents.yaml,metrics.yaml,project.yaml}

# Create docker files
touch writers-room-x/docker/{Dockerfile.api,Dockerfile.ui}

# Create root files
touch writers-room-x/{docker-compose.yml,.env.example,README.md}
touch writers-room-x/api/{pyproject.toml,requirements.txt}

echo "Structure created successfully"
