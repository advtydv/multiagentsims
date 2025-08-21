# Research Analysis Artifacts

This folder contains all analysis outputs for the information asymmetry simulation research paper.

## 📊 Main Findings Visualizations

1. **finding1_open_vs_closed.png** - 20-round comparison of open vs closed information systems showing revenue accumulation, task completion rates, and efficiency metrics

2. **finding2_model_comparison.png** - Performance analysis across different AI models (o3, o3-mini, gpt-4.1) demonstrating the sweet spot phenomenon

3. **finding3_uncooperative_impact.png** - Impact analysis of uncooperative agents on system performance in open vs closed settings

4. **finding4_cascade_effects.png** - Information manipulation cascade patterns and recovery dynamics

5. **finding5_asymmetry_variations.png** - Performance metrics across different initial information distributions (10%, 15%, 20%, 100%)

## 🎯 Additional Insights

6. **additional_learning_curves.png** - Learning and adaptation patterns over time comparing open vs closed systems

7. **additional_cooperation_emergence.png** - Network formation and cooperation evolution dynamics

8. **additional_critical_transitions.png** - Phase transitions and efficiency frontiers in system behavior

9. **surprising_discoveries.png** - Key unexpected findings including the uncooperative agent paradox

## 📄 Data Files

- **simulation_catalog.csv** - Complete inventory of all 122 simulations with metadata
- **RESEARCH_FINDINGS_SUMMARY.md** - Comprehensive written analysis of all findings

## 🔧 Analysis Scripts

- **analyze_simulations.py** - Initial simulation scanning and cataloging
- **comprehensive_analysis.py** - Full analysis pipeline for all findings
- **focused_analysis.py** - Targeted analysis using pre-computed metrics
- **generate_remaining_plots.py** - Plot generation for findings 2-5
- **create_additional_findings.py** - Additional insights and surprising discoveries
- **additional_analysis.py** - Extended analysis and summary generation

## 📈 Key Statistics

- **Total Simulations Analyzed**: 122
- **Simulations with Complete Metrics**: 36
- **Models Tested**: 6 (o3, o3-mini, gpt-4.1, gpt-4.1-mini, o4-mini, gpt-5)
- **System Configurations**: Open (60) vs Closed (62)
- **Uncooperative Agent Tests**: 18
- **Total Events Processed**: >50,000

## 🎓 Usage for Paper

All visualizations are publication-ready at 300 DPI. The findings support:

1. **Main argument**: Closed systems outperform open systems in longer timescales
2. **Model selection**: Moderate-capability models achieve optimal balance
3. **Security insights**: Open systems naturally resilient to bad actors
4. **Design implications**: 15-25% initial information distribution is optimal
5. **Surprising discovery**: Uncooperative agents win in open systems but lose in closed

## 📊 Reproduction

To reproduce these analyses:

```bash
# 1. Scan and catalog simulations
python analyze_simulations.py

# 2. Generate main findings plots
python focused_analysis.py

# 3. Create additional visualizations
python create_additional_findings.py
```

All raw simulation logs are preserved in `../logs/` for independent verification.