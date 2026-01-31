"""Main API router combining all routes."""

from fastapi import APIRouter

from . import (
    health,
    agent,
    agents,
    auth,
    db,
    graph,
    index,
    search,
    query,
    analyze,
    spec,
    tasks,
    plan,
    team,
    research,
    review,
    embed,
    rules,
    context,
    feature,
    projectmd,
    skills,
    stats,
    multiuser,
)

api_router = APIRouter(prefix="/api")

# Health & status
api_router.include_router(health.router)

# Authentication
api_router.include_router(auth.router)

# Agent operations
api_router.include_router(agent.router)
api_router.include_router(agents.router)
api_router.include_router(skills.router)

# Database management
api_router.include_router(db.router)

# Graph queries (for MCP server proxy)
api_router.include_router(graph.router)

# Indexing
api_router.include_router(index.router)

# Search & queries
api_router.include_router(search.router)
api_router.include_router(query.router)

# Analytics
api_router.include_router(analyze.router)

# Planning & specifications
api_router.include_router(spec.router)
api_router.include_router(tasks.router)
api_router.include_router(plan.router)
api_router.include_router(feature.router)

# Team & collaboration
api_router.include_router(team.router)
api_router.include_router(research.router)
api_router.include_router(review.router)

# Embeddings
api_router.include_router(embed.router)

# Configuration
api_router.include_router(rules.router)
api_router.include_router(context.router)

# Documentation generation
api_router.include_router(projectmd.router)

# Statistics
api_router.include_router(stats.router)

# Multiuser collaboration
api_router.include_router(multiuser.router)
