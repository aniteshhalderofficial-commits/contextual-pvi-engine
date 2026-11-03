# Data Pipeline Storage & Reproduction Guide

## 1. Purpose

This document explains the storage structure, processing workflow, and reproduction steps for the men's T20/IT20 Cricsheet data pipeline used by the Contextual Player Value Index (PVI) Engine.

The data pipeline is responsible for:

1. Acquiring Cricsheet match data.
2. Storing the raw JSON match files.
3. Parsing match, innings, and delivery information.
4. Building canonical processed datasets.
5. Validating the processed datasets.
6. Creating a representative sample dataset.
7. Providing a Python data-access interface for downstream analytical modules.

---

## 2. Storage Structure

The relevant project structure is:

```text
contextual-pvi-engine/
│
├── data/
│   ├── raw/
│   │   └── cricsheet/
│   │       ├── archive/
│   │       │   └── all_male_json.zip
│   │       └── matches/
│   │           └── *.json
│   │
│   ├── processed/
│   │   ├── match_metadata.csv
│   │   ├── innings.csv
│   │   └── deliveries.csv
│   │
│   └── sample/
│       └── deliveries_sample_1082591.csv
│
├── docs/
│   ├── data_dictionary.md
│   ├── validation_report.md
│   └── data_pipeline.md
│
└── src/
    └── data_pipeline/
        ├── inventory.py
        ├── parser.py
        ├── build_dataset.py
        ├── create_sample.py
        ├── validate_dataset.py
        └── data_access.py