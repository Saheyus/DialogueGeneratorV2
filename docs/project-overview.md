# Project Overview - DialogueGenerator

## Project Information

- **Project Name**: DialogueGenerator
- **Type**: Multi-part application (Frontend Web + Backend API)
- **Primary Language**: TypeScript (Frontend), Python (Backend)
- **Architecture**: Component-based SPA (Frontend) + REST API (Backend)
- **Repository Structure**: Multi-part (2 distinct parts)

## Executive Summary

DialogueGenerator is an AI-assisted dialogue generation tool for role-playing games. It interfaces with Large Language Models (LLMs) and relies on an existing Game Design Document (GDD) to generate Unity-compatible dialogue nodes.

### Key Capabilities

1. **GDD Data Loading**: Loads Game Design Document from JSON files extracted from Notion
2. **Context Selection**: Allows users to select context (characters, locations, items, etc.)
3. **Dialogue Generation**: Generates Unity JSON dialogue nodes using LLM
4. **Editing & Validation**: Facilitates writing, evaluation, and validation of dialogues
5. **Production Integration**: Integrates with game production pipeline (Unity JSON export, Git commit)

## Project Parts

### Part 1: Frontend (Web Application)

- **Type**: React Single-Page Application
- **Root Path**: `frontend/`
- **Technologies**: React 18, TypeScript, Vite, Zustand, React Query
- **Entry Points**: `src/main.tsx`, `index.html`
- **Purpose**: User interface for dialogue generation

### Part 2: Backend API

- **Type**: REST API
- **Root Path**: `api/`
- **Technologies**: FastAPI, Python, Pydantic
- **Entry Point**: `main.py`
- **Purpose**: API endpoints for dialogue generation, context management, and configuration

## Technology Stack Summary

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.2.0
- **Build Tool**: Vite 4.4.0
- **State Management**: Zustand 4.4.0
- **Data Fetching**: React Query 5.90.12
- **Routing**: React Router 6.20.0

### Backend
- **Framework**: FastAPI 0.104.0+
- **Language**: Python 3.10+
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic 2.0+
- **LLM Integration**: OpenAI SDK 1.15+

## Architecture Type

**Multi-Part Application** with:
- Clear separation between frontend and backend
- REST API communication
- Independent deployment capability
- Shared data models and constants

## Quick Reference

### Tech Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Python
- **State Management**: Zustand (Frontend)
- **API Communication**: REST JSON

### Entry Points
- **Frontend**: `frontend/src/main.tsx`
- **Backend**: `api/main.py`

### Architecture Pattern
- **Frontend**: Component-based SPA
- **Backend**: Layered REST API

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js and npm
- OpenAI API key

### Quick Start
```bash
# Install dependencies
npm run install:all

# Start development servers
npm run dev

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:4243
```

See `development-guide.md` for detailed setup instructions.

## Project Structure

```
DialogueGenerator/
├── frontend/          # React frontend application
├── api/              # FastAPI backend API
├── core/             # Core business logic
├── services/         # Application services
├── models/           # Data models
├── tests/            # Test suite
├── config/           # Configuration files
├── data/             # Data storage
├── scripts/          # Build and utility scripts
└── docs/             # Documentation
```

## Key Features

### Dialogue Generation
- Context-aware dialogue generation
- Multiple variants generation
- Unity JSON format output
- Token estimation and budget management

### Context Management
- GDD element selection (characters, locations, items, etc.)
- Context building and summarization
- Linked element detection
- Region and sub-location filtering

### Graph Editor
- Visual dialogue graph editing
- Node-based dialogue structure
- AI-assisted generation
- Export/import capabilities

### Configuration
- System prompt customization
- Scene instruction templates
- Author profile management
- Context field configuration

## Documentation Index

### Architecture
- [Frontend Architecture](./architecture-frontend.md)
- [Backend Architecture](./architecture-api.md)
- [Integration Architecture](./integration-architecture.md)

### API Documentation
- [Backend API Contracts](./api-contracts-api.md)
- [Frontend API Client](./api-contracts-frontend.md)

### Data Models
- [Backend Data Models](./data-models-api.md)
- [Frontend Data Models](./data-models-frontend.md)

### Development
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)
- [Source Tree Analysis](./source-tree-analysis.md)

### State Management
- [Frontend State Management](./state-management-frontend.md)

### UI Components
- [UI Component Inventory](./ui-component-inventory-frontend.md)

### Technology
- [Technology Stack](./technology-stack.md)

## Links to Detailed Documentation

- **Master Index**: [index.md](./index.md) (primary entry point)
- **API Documentation**: [README_API.md](../README_API.md)
- **Main README**: [README.md](../README.md)
- **Security Guide**: [SECURITY.md](./SECURITY.md)
- **Testing Guide**: [TESTING.md](./TESTING.md)

## Next Steps

For brownfield PRD creation:
- Reference this documentation when creating PRD
- Point PRD workflow to: `docs/index.md`
- Use architecture documents for technical context

For development:
- See `development-guide.md` for setup
- See `architecture-*.md` for technical details
- See API contracts for endpoint documentation
