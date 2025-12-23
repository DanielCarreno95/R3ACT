# GitHub Repository Setup - Final Commands

## Quick Setup for GitHub Repository

Your repository URL: `https://github.com/DanielCarreno95/R3ACT.git`

### Step 1: Navigate to Project Directory

```bash
cd analytics_cup_research-main
```

### Step 2: Initialize Git (if not already done)

```bash
git init
git branch -M main
```

### Step 3: Add All Files

```bash
git add .
```

### Step 4: Verify What Will Be Committed

```bash
git status
```

**Important**: Verify that:
- ✅ `submission.ipynb` is included
- ✅ `src/` folder is included
- ✅ `README.md` is included
- ✅ `ABSTRACT.md` is included
- ✅ `requirements.txt` is included
- ✅ `streamlit_app.py` is included
- ❌ No `.csv`, `.json`, or `.jsonl` data files
- ❌ No `__pycache__/` folders

### Step 5: Create Initial Commit

```bash
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
```

### Step 6: Connect to GitHub Repository

```bash
git remote add origin https://github.com/DanielCarreno95/R3ACT.git
```

If remote already exists:
```bash
git remote set-url origin https://github.com/DanielCarreno95/R3ACT.git
```

Verify remote:
```bash
git remote -v
```

### Step 7: Push to GitHub

```bash
git push -u origin main
```

**Note**: If you get authentication errors:
- Use GitHub Personal Access Token instead of password
- Or configure SSH keys

### Step 8: Verify on GitHub

After pushing, check on GitHub:
1. All files are visible
2. `submission.ipynb` is in root
3. `src/` folder structure is correct
4. README displays properly
5. No large files warning

## Alternative: Using GitHub Desktop

1. Open GitHub Desktop
2. File → Add Local Repository
3. Select `analytics_cup_research-main` folder
4. Click "Publish repository"
5. Select `DanielCarreno95/R3ACT`
6. Click "Publish repository"

## Troubleshooting

### Authentication Error

If `git push` fails with authentication:
```bash
# Use Personal Access Token
# Or switch to SSH
git remote set-url origin git@github.com:DanielCarreno95/R3ACT.git
```

### Large Files Warning

If GitHub warns about large files:
```bash
# Check .gitignore is working
git check-ignore -v *.csv
git check-ignore -v *.json

# Remove from cache if accidentally added
git rm --cached *.csv
git rm --cached *.json
```

### Repository Already Has Content

If repository already has content:
```bash
git pull origin main --allow-unrelated-histories
# Resolve any conflicts
git push -u origin main
```

## Final Verification Checklist

Before submitting to competition:

- [ ] Repository is on `main` branch
- [ ] `submission.ipynb` is in root directory
- [ ] `ABSTRACT.md` is included (498 words)
- [ ] All code is in `src/` folder
- [ ] `requirements.txt` includes all dependencies
- [ ] `README.md` is in English
- [ ] `streamlit_app.py` is included
- [ ] No data files (`.csv`, `.json`, `.jsonl`) are committed
- [ ] `.gitignore` excludes data files and cache
- [ ] All documentation is in English
- [ ] Repository is accessible on GitHub

## Next Steps After Push

1. **Submit to Pretalx**: https://pretalx.pysport.org
   - Repository URL: `https://github.com/DanielCarreno95/R3ACT`
   - Include abstract from `ABSTRACT.md`

2. **Deploy Streamlit Dashboard** (Optional):
   - Go to: https://share.streamlit.io
   - Connect repository
   - Deploy `streamlit_app.py`

3. **Test in Clean Environment**:
   ```bash
   python -m venv test_env
   source test_env/bin/activate  # Windows: test_env\Scripts\activate
   pip install -r requirements.txt
   jupyter notebook submission.ipynb
   ```

## Success!

Your repository is now ready for submission! 🚀

