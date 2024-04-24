# Digital Musicology (DH-401): Generating Expressive Performance

This repository contains our solution for [the second assignment](https://hackmd.io/@RFMItzZmQbaIqDdVZ0DovA/H16QgvgeC) of Digital Musicology (DH-401) course. The assignment consisted of three tasks: (A) comparing performed and unperformed versions of a piece of our choice, (B) use our observations to make original MIDI more expressive, and (C) listen to the generated MIDI and evaluate how human-like it is. We used _Schubert Impromptu Op. 90 No. 3_ in all our experiments.

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

## Results

Generated MIDI is located in `results` dir. Our final MIDI is called `generated_midi_with_pedal.mid`. We provide corresponding audio version, however, it is better to use piano roll (like [this one](https://signal.vercel.app/edit)).

## Project Structure

The project structure is as follows:

```bash
├── data                         # dir for all data, including raw and processed datasets
│   └── asap-dataset
├── results                      # dir with original midi and its generated_versions
│   ├── generated_midi.mid
│   ├── generated_midi.wav
│   ├── generated_midi_with_pedal.mid
│   ├── generated_midi_with_pedal.wav
│   ├── original_midi.mid
│   ├── original_midi.wav
│   ├── xml_midi.mid
│   └── xml_midi.wav
├── experiments.ipynb            # used for experiments
├── run_transfer.py              # Core script, trasfer midi to performed version
├── README.md                    # this file
├── requirements.txt             # list of required packages
├── observations.md              # observations/ideas to implement
└── src                          # package with core implementations
    ├── interpret.py             # core algorithms for MIDI generation (main source)
    ├── data.py                  # data loading and processing, used for experiments
    ├── midi_transfer.py         # used for experiments (outdated)
    ├── estimators.py            # used for experiments (outdated)
    ├── __init__.py
    └── plots.py                 # used for experiments (outdated)
```

## Authors

The project was done by:

- Petr Grinberg
- Marco Bondaschi
- Ismaïl Sahbane
- Ben Erik Kriesel
