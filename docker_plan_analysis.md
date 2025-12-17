I've created a comprehensive plan for Dockerizing your forensic psychiatry RAG application.

  Summary

  The plan will help you:

  1. Create Docker containers for both backend (FastAPI) and frontend (Next.js)
  2. Pre-configure everything with your API keys so your friend doesn't need to set anything up
  3. Export the images to files (~350MB compressed) that you can send to your friend
  4. Provide simple instructions - your friend will just run 3 commands and open their browser

  Your workflow:
  - Build Docker images on your Mac (takes ~10 mins)
  - Test locally to make sure everything works
  - Export images to compressed files
  - Package with docker-compose.yml, .env (with your keys), and README
  - Send to your friend (via USB, cloud, etc.)

  Your friend's workflow:
  - Install Docker Desktop (one-time setup)
  - Load the 2 image files (2 commands)
  - Start the app (1 command: docker-compose up -d)
  - Open browser to http://localhost:3000
  - Done!

  The plan includes detailed testing steps for you to verify everything works before handing it off.

────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Docker Setup Plan for Forensic Psychiatry RAG Application

 Overview

 Create a Docker-based deployment package for a non-technical user. The user will build Docker images,
 export them, and provide pre-configured files so their friend can run the application with just a few
 copy/paste commands.

 User Requirements (from Q&A)

 - API Keys: Friend will use the user's API keys (pre-configured in .env)
 - Delivery: Pre-built Docker images (user exports ~600MB image files)
 - Friend's Tech Level: Can copy/paste Terminal commands

 Application Architecture

 - Backend: FastAPI (Python 3.11) + LlamaIndex + ChromaDB on port 8000
 - Frontend: Next.js 16 (Node 22) on port 3000
 - Data: 7 sample cases (21 files) + pre-built ChromaDB vector database (~3.3MB)

 ---
 Phase 1: Create Docker Configuration Files

 1.1 Backend Dockerfile

 File: backend/Dockerfile

 Strategy: Multi-stage build with Python 3.11-slim
 - Stage 1: Builder - install dependencies in virtual environment
 - Stage 2: Runtime - copy venv, application code, and data
 - Include pre-built ChromaDB in image
 - Volume mount for persistence
 - Health check on /health endpoint

 Key points:
 - Copy entire data/ directory (includes cases + chroma_db)
 - Use slim Python image (~450MB final size)
 - Expose port 8000
 - CMD: uvicorn main:app --host 0.0.0.0 --port 8000

 1.2 Frontend Dockerfile

 File: frontend/Dockerfile

 Strategy: Multi-stage build with Node 22-alpine for minimal size
 - Stage 1: Install production dependencies
 - Stage 2: Install all deps + build Next.js
 - Stage 3: Runtime with standalone output (~150MB final size)
 - Non-root user (nextjs) for security
 - Disable telemetry

 Key points:
 - Requires standalone output mode (see 1.3)
 - Copy .next/standalone and .next/static
 - Expose port 3000
 - CMD: node server.js

 1.3 Update Next.js Config

 File: frontend/next.config.ts

 Change: Add standalone output mode
 const nextConfig: NextConfig = {
   output: 'standalone',
 };

 This enables Next.js to create a self-contained production build.

 1.4 Backend .dockerignore

 File: backend/.dockerignore

 Exclude:
 - venv/ (rebuilt in container)
 - __pycache__/
 - *.pyc
 - .env (will be provided separately)
 - .git/

 1.5 Frontend .dockerignore

 File: frontend/.dockerignore

 Exclude:
 - node_modules/ (rebuilt in container)
 - .next/ (rebuilt in container)
 - .env*
 - .git/

 ---
 Phase 2: Docker Compose Configuration

 2.1 Docker Compose File

 File: docker-compose.yml (in project root)

 Services:
 1. backend:
   - Image: fpamed-backend:latest (pre-built)
   - Environment variables from .env file
   - Volume: chroma_data for persistence
   - Internal network only (not exposed to host)
   - Health check enabled
 2. frontend:
   - Image: fpamed-frontend:latest (pre-built)
   - Environment: NEXT_PUBLIC_API_URL=http://backend:8000
   - Ports: 3000:3000 (exposed to host)
   - Depends on backend health check
   - Internal network

 Networks: fpamed-network (bridge driver)

 Volumes: chroma_data (named volume for ChromaDB persistence)

 Important: Use image: field (not build:) since we're providing pre-built images.

 2.2 Environment File

 File: .env (in project root)

 Create with user's actual API keys:
 # Required API Keys
 ANTHROPIC_API_KEY=sk-ant-[USER_FILLS_THIS_IN]
 OPENAI_API_KEY=sk-proj-[USER_FILLS_THIS_IN]

 # Model Configuration (defaults provided)
 ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
 EMBEDDING_MODEL=text-embedding-3-small

 # Optional Settings (use defaults)
 LLM_TEMPERATURE=0.3
 LLM_MAX_TOKENS=1000
 TOP_K_RETRIEVAL=5

 User will need to fill in their actual API keys before building.

 ---
 Phase 3: Testing the Docker Setup

 3.1 Build Images

 # From project root
 docker build -t fpamed-backend:latest ./backend
 docker build -t fpamed-frontend:latest ./frontend

 Expected build time: 5-10 minutes first time
 Expected sizes:
 - Backend: ~450MB
 - Frontend: ~150MB

 3.2 Start Services

 docker-compose up -d

 Wait 30-60 seconds for initialization.

 3.3 Verify Health

 # Check container status
 docker-compose ps
 # Backend should show "healthy"

 # Test health endpoint
 curl http://localhost:8000/health
 # Should return: {"status":"ok","vector_db":"connected","documents_loaded":14}

 3.4 Test Functionality

 Open browser to http://localhost:3000

 Test cases:
 1. ✅ Chat interface loads
 2. ✅ Case dropdown shows 7 cases
 3. ✅ Ask: "What is case_001 about?" → Returns answer with sources
 4. ✅ Select case_001, ask question → Only returns case_001 sources
 5. ✅ Click "Find Similar Cases", search "competency" → Returns relevant cases
 6. ✅ Click "Clear Conversation" → Messages cleared

 3.5 Test Persistence

 # Stop containers
 docker-compose down

 # Restart
 docker-compose up -d

 # Verify data persisted
 curl http://localhost:8000/health
 # Should still show 14 documents

 3.6 Clean Up

 docker-compose down

 ---
 Phase 4: Export Images for Friend

 4.1 Save Images to Files

 # Export backend image (~450MB compressed)
 docker save fpamed-backend:latest | gzip > fpamed-backend.tar.gz

 # Export frontend image (~150MB compressed)
 docker save fpamed-frontend:latest | gzip > fpamed-frontend.tar.gz

 Total size: ~300-400MB compressed (will expand to ~600MB when loaded)

 4.2 Create Package Directory

 Create a folder with everything the friend needs:

 fpamed-docker-package/
 ├── fpamed-backend.tar.gz
 ├── fpamed-frontend.tar.gz
 ├── docker-compose.yml
 ├── .env
 └── README.md (instructions for friend)

 ---
 Phase 5: Create Documentation

 5.1 Friend's Setup Instructions

 File: README.md (in package directory)

 Contents:
 1. Prerequisites:
   - Install Docker Desktop (link for Mac/Windows/Linux)
   - How to verify Docker is running
 2. Setup Steps (5 steps):
 # Step 1: Load images
 docker load < fpamed-backend.tar.gz
 docker load < fpamed-frontend.tar.gz

 # Step 2: Start application
 docker-compose up -d

 # Step 3: Wait 30 seconds

 # Step 4: Open browser
 # Go to: http://localhost:3000

 # Step 5: Start chatting!
 3. Stopping the App:
 docker-compose down
 4. Troubleshooting:
   - Port conflicts (if 3000 in use)
   - Docker not running
   - Images failed to load

 5.2 Testing Notes for User

 File: DOCKER_BUILD_NOTES.md (for user's reference)

 Contents:
 - Build commands used
 - Export process
 - Testing checklist results
 - File sizes and transfer recommendations
 - How to update images if needed

 ---
 Critical Files Summary

 New Files to Create:
 1. /Users/JudeHoffner/dev/fpamed/backend/Dockerfile - Backend container build
 2. /Users/JudeHoffner/dev/fpamed/backend/.dockerignore - Exclude unnecessary files
 3. /Users/JudeHoffner/dev/fpamed/frontend/Dockerfile - Frontend container build
 4. /Users/JudeHoffner/dev/fpamed/frontend/.dockerignore - Exclude unnecessary files
 5. /Users/JudeHoffner/dev/fpamed/docker-compose.yml - Service orchestration
 6. /Users/JudeHoffner/dev/fpamed/.env - API keys configuration
 7. Package README.md - Friend's setup instructions
 8. DOCKER_BUILD_NOTES.md - User's reference notes

 Files to Modify:
 1. /Users/JudeHoffner/dev/fpamed/frontend/next.config.ts - Add output: 'standalone'

 ---
 Implementation Order

 1. Create backend Dockerfile and .dockerignore
 2. Update frontend next.config.ts
 3. Create frontend Dockerfile and .dockerignore
 4. Create docker-compose.yml
 5. Create .env file (user adds their API keys)
 6. Build and test locally (Phase 3)
 7. Export images (Phase 4)
 8. Create README for friend (Phase 5)
 9. Package everything together

 ---
 Delivery Package Contents

 What the friend receives:
 - fpamed-backend.tar.gz (~250MB)
 - fpamed-frontend.tar.gz (~100MB)
 - docker-compose.yml
 - .env (with user's API keys)
 - README.md (5-step setup guide)

 Friend's experience:
 1. Install Docker Desktop (one-time)
 2. Run 2 commands to load images
 3. Run 1 command to start app
 4. Open browser to localhost:3000
 5. Start using the application

 Total time for friend: ~10 minutes (after Docker installation)

 ---
 Key Design Decisions

 ✅ Pre-built images: Friend doesn't need to build (faster, simpler)
 ✅ Pre-configured .env: API keys already filled in
 ✅ Pre-populated ChromaDB: No need to run ingestion
 ✅ Multi-stage builds: Smaller final images
 ✅ Production Next.js: Optimized performance
 ✅ Volume persistence: ChromaDB data survives container restarts
 ✅ Health checks: Frontend waits for backend to be ready
 ✅ Copy/paste commands: No need to understand Docker internals