#!/bin/bash
# GitHub Repository Setup Script for R3ACT
# Run this script to prepare and push to GitHub

echo "=========================================="
echo "R3ACT GitHub Repository Setup"
echo "=========================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -M main
else
    echo "Git repository already initialized"
fi

# Add all files
echo "Adding files to git..."
git add .

# Check status
echo ""
echo "Files to be committed:"
git status --short

# Create commit
echo ""
read -p "Create commit? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "R3ACT: Resilience, Reaction and Recovery Analysis of Critical Transitions

Complete implementation for SkillCorner X PySport Analytics Cup - Research Track

Features:
- 3 core metrics: CRT, TSI, GIRI
- Parametrizable critical event detection
- Configurable event weighting system
- Temporal windows: 2/5/10 minutes
- Global baseline calculation across all matches
- Interactive Streamlit dashboard
- Full validation and testing

All code in src/ folder
Data loads directly from SkillCorner GitHub repository
Notebook: submission.ipynb
Abstract: ABSTRACT.md (498 words)"
    
    echo ""
    echo "Commit created successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Add remote: git remote add origin https://github.com/DanielCarreno95/R3ACT.git"
    echo "2. Push: git push -u origin main"
else
    echo "Commit cancelled"
fi

echo ""
echo "Setup complete!"

