# Digital Musicology (DH-401): Generating Expressive Performance

This repository contains our solution for [the second assignment](https://hackmd.io/@RFMItzZmQbaIqDdVZ0DovA/H16QgvgeC) of Digital Musicology (DH-401) course. **TODO**

We used [Aligned Scores and Performances (ASAP) dataset](https://github.com/fosfrancesco/asap-dataset) for the assignment.

## Installation

Follow this steps to reproduce our work:

0. (Optional) Create and activate new environment using [`conda`](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html) or `venv` ([`+pyenv`](https://github.com/pyenv/pyenv)).

   a. `conda` version:

   ```bash
   # create env
   conda create -n project_env python=PYTHON_VERSION

   # activate env
   conda activate project_env
   ```

   b. `venv` (`+pyenv`) version:

   ```bash
   # create env
   ~/.pyenv/versions/PYTHON_VERSION/bin/python3 -m venv project_env

   # alternatively, using default python version
   python3 -m venv project_env

   # activate env
   source project_env
   ```

1. Install all required packages

   ```bash
   pip install -r requirements.txt
   ```

2. Install `pre-commit`:

   ```bash
   pre-commit install
   ```

3. Download dataset:

   ```bash
   mkdir data
   cd data
   git clone https://github.com/fosfrancesco/asap-dataset.git
   ```

4. If you want to convert MIDI to wav file:

   ```bash
   apt-get install fluidsynth > /dev/null
   cp /usr/share/sounds/sf2/FluidR3_GM.sf2 ./font.sf2
   ```

## Run code

To transfer MIDI from unperformed version to a performed one, run the following command:

```bash
python3 run_transfer.py
```

See `run_transfer.py --help` for command-line arguments.

## Project Structure

The project structure is as follows:

```bash
├── data                         # dir for all data, including raw and processed datasets
│   └── asap-dataset
├── experiments.ipynb            # scripts for figures and tables
├── run_transfer.py              # trasfer midi to performed version
├── README.md                    # this file
├── requirements.txt             # list of required packages
└── src                          # package with core implementations
    ├── data.py                  # data loading and processing
    ├── estimators.py            # estimators for Task_A
    ├── __init__.py
    ├── onset_distribution.py    # methods and plots used for Task_B
    └── plots.py                 # plot functions for Task_A
```

## Authors

The project was done by:

- Petr Grinberg
- Marco Bondaschi
- Ismaïl Sahbane
- Ben Erik Kriesel
