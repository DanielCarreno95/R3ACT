# R3ACT Deployment Guide

## Running the Streamlit Dashboard

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Production Deployment

#### Option 1: Streamlit Cloud (Recommended)

1. Push your repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file path: `streamlit_app.py`
5. Deploy!

#### Option 2: Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t r3act-dashboard .
docker run -p 8501:8501 r3act-dashboard
```

## GitHub Repository Setup

### Repository Structure

```
analytics_cup_research-main/
├── .gitignore
├── README.md
├── ABSTRACT.md
├── LICENSE
├── requirements.txt
├── submission.ipynb
├── streamlit_app.py
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── event_detector.py
│   ├── baseline_calculator.py
│   ├── metrics_calculator.py
│   └── r3act_system.py
└── .streamlit/
    └── config.toml (optional)
```

### Git Setup

1. Initialize repository (if not already):
```bash
git init
git branch -M main
```

2. Add all files:
```bash
git add .
```

3. Commit:
```bash
git commit -m "Initial R3ACT system implementation"
```

4. Create GitHub repository and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/r3act-analytics-cup.git
git push -u origin main
```

### Important Notes

- **Do NOT commit large data files** - Data is loaded directly from SkillCorner GitHub
- **Ensure `submission.ipynb` is in root** - Required by competition rules
- **Abstract must be in repository** - Can be in `ABSTRACT.md` or as separate file
- **All code in `src/` folder** - As per competition requirements

## Competition Submission

### Checklist Before Submission

- [ ] `submission.ipynb` in root directory
- [ ] Abstract (max 500 words) included
- [ ] All code in `src/` folder
- [ ] `requirements.txt` includes all dependencies
- [ ] README.md with clear instructions
- [ ] Repository is on `main` branch
- [ ] No large data files committed
- [ ] Notebook runs in clean environment
- [ ] Streamlit app works (optional but recommended)

### Submission Steps

1. **Finalize Repository**:
   - Ensure all code is committed
   - Test that `submission.ipynb` runs correctly
   - Verify abstract is included

2. **Submit to Pretalx**:
   - Go to [pretalx.pysport.org](https://pretalx.pysport.org)
   - Submit your GitHub repository URL
   - Include any additional notes

3. **Verify Submission**:
   - Check that repository is public (if required)
   - Ensure all files are accessible
   - Test notebook execution in clean environment

## Streamlit Cloud Deployment

### Steps

1. **Prepare Repository**:
   - Ensure `streamlit_app.py` is in root
   - Verify `requirements.txt` includes streamlit
   - Test locally first

2. **Deploy to Streamlit Cloud**:
   - Sign up at [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repository
   - Set main file: `streamlit_app.py`
   - Click "Deploy"

3. **Share Dashboard**:
   - Streamlit Cloud provides a public URL
   - Share with stakeholders
   - Update README with dashboard link

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure `src/` folder structure is correct
   - Check that `__init__.py` exists in `src/`

2. **Data Loading Issues**:
   - Verify internet connection (data loads from GitHub)
   - Check SkillCorner repository is accessible

3. **Streamlit Not Loading**:
   - Verify all dependencies installed
   - Check `streamlit_app.py` is in root directory
   - Review error messages in terminal

4. **Performance Issues**:
   - First load may be slow (loading all matches)
   - Consider caching results
   - Use `load_tracking=False` for faster initial load

## Support

For issues or questions:
- Check README.md for documentation
- Review validation reports
- Test with sample data first

