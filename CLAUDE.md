# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Art Factory is a Django-first web application for managing AI-generated art using various providers like fal.ai, Replicate, and civitai. The project commits to leveraging Django's mature ecosystem and established patterns to minimize architectural complexity and accelerate development.

## Session Start
@.claude/MOC.md



## Documentation Structure

The project documentation is organized into focused files:

- **vision.md**: Project purpose, value proposition, and target user
- **concepts.md**: Core domain model and business concepts
- **features.md**: Functional requirements and implementation phases
- **ux.md**: User interface requirements and interaction patterns
- **requirements.md**: Technical requirements and deployment constraints
- **design.md**: Detailed technical architecture (implementation-specific)

## Architecture

### Core Domain Concepts

The application follows a factory abstraction pattern:

- **Products**: Generated media files (images, videos, audio) with metadata
- **Orders**: User requests containing base parameters and production line specification
- **Order Items**: Individual product creation tasks derived from orders
- **Factory Machines**: Provider-specific implementations for generating products
- **Providers**: External AI services (fal.ai, Replicate, civitai)
- **Parameter Sets**: Flexible JSON-based parameter handling for different models

### Component Hierarchy

**Product Factory Inheritance:**
- BaseProductFactory (common validation/infrastructure)
- ProviderProductFactory (provider-specific setup)
- ModelModalityProductFactory (modality-specific logic)
- ModelSpecificFactory (model-specific parameters)

### Key Features

- Smart parameter expansion with token interpolation
- Real-time updates (implementation approach TBD)
- Template and favorites system
- Project organization and management
- Background task processing for production workflows

## Memory Notes

- Always read ./.claude/kb/MOC.md at the start of each session to understand local knowledge

## (Rest of the file remains unchanged)