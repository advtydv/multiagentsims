# Repository Issues Report

## Executive Summary
This report identifies all issues found in the repository that should be addressed before uploading to GitHub.

## Critical Issues

### 1. Missing .gitignore File
**Status**: ❌ Critical
- No .gitignore file exists in the repository
- This leads to tracking of unnecessary files

### 2. Exposed API Key in config.py
**Status**: ❌ Critical
- Line 27 in `/code/config.py` contains a hardcoded OpenAI API key:
  ```python
  'openai': os.getenv('OPENAI_API_KEY', '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'),
  ```
- This should NEVER be committed to version control

## High Priority Issues

### 3. Unnecessary System Files
**Status**: ⚠️ High Priority
- `.DS_Store` file in root directory (macOS system file)
- `__pycache__` directory in `/code/` 
- These should not be in version control

### 4. Test Files in Repository
**Status**: ⚠️ High Priority
- Multiple test files that appear to be development/debugging files:
  - `test_parallel_vs_sequential.py`
  - `test_parallelization.py`
  - `test_pf_simulation.py`
- Consider if these should be in a separate test directory or excluded

### 5. Simulation Results in Repository
**Status**: ⚠️ High Priority
- `/code/pf_results/` directory contains 19 JSON result files
- These appear to be output files from running simulations
- Result files typically should not be version controlled

## Medium Priority Issues

### 6. Duplicated Functionality
**Status**: ⚠️ Medium Priority
- Two main entry point files exist:
  - `main.py` - Appears to be the original version
  - `pf_main_v2.py` - Appears to be a newer version with "pf_" prefix
- This creates confusion about which version to use

### 7. Mixed Naming Conventions
**Status**: ⚠️ Medium Priority
- Original files: `agent.py`, `environment.py`, `institution.py`, `main.py`
- Preference falsification files: `pf_agent.py`, `pf_environment.py`, `pf_main_v2.py`
- This suggests two different simulation systems coexisting

### 8. Duplicate Configuration Files
**Status**: ⚠️ Medium Priority
- `parameters.py` - Contains simulation parameters
- `config.py` - Also contains simulation parameters
- These appear to serve similar purposes with overlapping configuration

### 9. Multiple README Files
**Status**: ⚠️ Medium Priority
- `/README.md` - Main repository README
- `/code/PF_README.md` - Preference falsification specific README
- Consider consolidating or clearly differentiating their purposes

## Low Priority Issues

### 10. Jupyter Notebook in Code Directory
**Status**: ℹ️ Low Priority
- `natural_lan_analysis.ipynb` contains analysis code
- Contains hardcoded file paths and API configuration sections
- Consider moving to a separate analysis directory

### 11. Client Implementation Files
**Status**: ℹ️ Low Priority
- Multiple API client files suggest the code supports various providers
- No issues found, but ensure no credentials are hardcoded

## Recommendations

### Immediate Actions Required:
1. **Create .gitignore file** with the following content:
   ```
   # macOS
   .DS_Store
   
   # Python
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   .Python
   
   # Environment
   .env
   venv/
   env/
   
   # IDE
   .vscode/
   .idea/
   *.swp
   
   # Results and outputs
   pf_results/
   simulation_results.json
   *.csv
   
   # Jupyter
   .ipynb_checkpoints/
   
   # API keys and secrets
   config.py
   ```

2. **Remove the hardcoded API key** from config.py immediately
3. **Clean the repository** of unnecessary files before committing

### Before Publishing:
1. Decide which simulation system to keep (original vs pf_)
2. Consolidate configuration files
3. Move test files to a proper test directory
4. Consider using environment variables for all sensitive configuration
5. Add a config.example.py file showing the structure without actual keys

### Repository Structure Recommendation:
```
publicgoods/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── code/
│   ├── agents/
│   ├── environment/
│   ├── api_clients/
│   └── config.example.py
├── tests/
├── analysis/
│   └── notebooks/
└── docs/
```

## Summary Statistics
- Total Critical Issues: 2
- Total High Priority Issues: 3
- Total Medium Priority Issues: 4
- Total Low Priority Issues: 2
- **Total Issues: 11**

## Next Steps
1. Address all critical issues immediately
2. Clean up the repository structure
3. Run `git status` to verify all unwanted files are removed
4. Consider squashing commits to remove any history of the API key