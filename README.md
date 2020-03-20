# SONIA

## Synopsis

SONIA is a python 3.6/2.7 software developed to infer selection pressures on features of amino acid CDR3 sequences. The inference is based on maximizing the likelihood of observing a selected data sample given a representative pre-selected sample. This method was first used in Elhanati et al (2014) to study thymic selection. For this purpose, the pre-selected sample can be generated internally using the OLGA software package, but SONIA allows it also to be supplied externally, in the same way the data sample is provided.

SONIA takes as input TCR CDR3 amino acid sequences, with or without per sequence lists of possible V and J genes suspected to be used in the recombination process for this sequence. Its output is selection factors for each amino acid ,(relative) position , CDR3 length combinations, and also for each V and J gene choice. These selection factors can be used to calculate sequence level selection factors which indicate how more or less represented this sequence would be in the selected pool as compared to the the pre-selected pool. These in turn could be used to calculate the probability to observe any sequence after selection and sample from the selected repertoire. 

## Version
Latest released version: 0.0.1

## Installation
SONIA is a python 2.7/3.6 software. It is available on PyPI and can be downloaded and installed through pip:

 ```pip install sonia```.

SONIA is also available on [GitHub](https://github.com/statbiophys/SONIA). The command line entry points can be installed by using the setup.py script:

 ```$ python setup.py install```.
## References

1. Sethna Z, Isacchini G, Dupic T, Mora T, Walczak AM, Elhanati Y, Population variability in the generation and thymic selection of T-cell repertoires, (2020) bioRxiv, https://doi.org/10.1101/2020.01.08.899682
2. Isacchini G, Sethna Z, Elhanati Y ,Nourmohammad A, Mora T, Walczak AM, On generative models of T-cell receptor sequences,(2019) bioRxiv, https://doi.org/10.1101/857722
3. Elhanati Y, Murugan A , Callan CGJ ,  Mora T , Walczak AM, Quantifying selection in immune receptor repertoires, PNAS July 8, 2014 111 (27) 9875-9880, https://doi.org/10.1073/pnas.1409572111
                                    
## Directory architecture
```
SONIA/
├── LICENSE
├── MANIFEST.in
├── README.md
├── data_seqs.txt
├── example_pipeline_script.py
├── gen_seqs.txt
├── setup.py
└── sonia
    ├── __init__.py
    ├── default_models
    │   ├── human_B_heavy
    │   │   ├── J_gene_CDR3_anchors.csv
    │   │   ├── V_gene_CDR3_anchors.csv
    │   │   ├── features.tsv
    │   │   ├── log.txt
    │   │   ├── model_marginals.txt
    │   │   └── model_params.txt
    │   ├── human_T_alpha
    │   │   ├── J_gene_CDR3_anchors.csv
    │   │   ├── V_gene_CDR3_anchors.csv
    │   │   ├── features.tsv
    │   │   ├── log.txt
    │   │   ├── model_marginals.txt
    │   │   └── model_params.txt
    │   ├── human_T_beta
    │   │   ├── J_gene_CDR3_anchors.csv
    │   │   ├── V_gene_CDR3_anchors.csv
    │   │   ├── features.tsv
    │   │   ├── log.txt
    │   │   ├── model_marginals.txt
    │   │   └── model_params.txt
    │   └── mouse_T_beta
    │       ├── J_gene_CDR3_anchors.csv
    │       ├── V_gene_CDR3_anchors.csv
    │       ├── features.tsv
    │       ├── log.txt
    │       ├── model_marginals.txt
    │       └── model_params.txt
    ├── evaluate.py
    ├── evaluate_model.py
    ├── generate.py
    ├── infer.py
    ├── plotting.py
    ├── sequence_generation.py
    ├── sonia.py
    ├── sonia_leftpos_rightpos.py
    ├── sonia_length_pos.py
    └── utils.py
```

## Command line console scripts and Examples

There are three command line console scripts (the scripts can still be called as executables if SONIA is not installed):
1. sonia-evaluate
  * evaluates Ppost, Pgen or selection factors of sequences according to a generative V(D)J model and selection model.
2. sonia-generate
  * generates CDR3 sequences, before (like olga) or after selection
3. sonia-infer
  * infers a selection model with respect to a generative V(D)J model

For any of them you can execute with the -h or --help flags to get the options.

### Quick Demo
After installing SONIA, we offer a quick demonstration of the console scripts. This will demonstrate generating and evaluating sequences and infer a selection model from the default model for human TCR beta chains that ships with SONIA. 

1. ```$ sonia-evaluate --humanTRB CASSTGNYGAFF --v_mask TRBV9 --j_mask TRBJ1-1 --ppost```
  * This computes Ppost,Pgen and Q of the TCR CASSTGNYGAFF,TRBV9,TRBJ1-1 (you should get ~1.3e-11, ~9.2e-12 and ~1.4 respectively)

2. ```$ sonia-generate --humanTRB -n 5 --pre```
  * Generate 5 human TRB CDR3 sequences from the pre-selection repertoire and print to stdout along with the V and J genes used to generate them.

3. ```$ sonia-generate --humanTRB -n 10000 --post -o example_seqs.txt```
  * This generates a file example_seqs.tsv and writes 10000 generated human TRB CDR3 sequences from the post-selection repertoire.

4. ```$ sonia-evaluate --humanTRB --ppost -i example_seqs.txt -m 5  -o example_evaluation.txt```
  * This reads in the first 5 sequences from the file we just generated, example_seqs.tsv, evaluates them and writes the results them to the file example_pgens.tsv
  
5. ```$ sonia-infer --humanTRB -i example_seqs.txt -o sel_model```
  * This reads in the full file example_seqs.txt, infers a selection model and saves to the folder sel_model

## Using the SONIA modules in a Python script (advanced users)
In order to incorporate the core algorithm into an analysis pipeline (or to write your own script wrappers) all that is needed is to import the modules. Each module defines some classes that only a few methods get called on.

The modules are:

| Module name                                    | Classes                                          |    
|------------------------------------------------|--------------------------------------------------|
| evaluate_model.py                 | EvaluateModel|
| sequence_generation.py        | SequenceGeneration|
|plotting.py.                               |Plotter|
| sonia_leftpos_rightpos.py        | SoniaLeftposRightpos|
| sonia_length_pos.py                | SoniaLengthPos |
| sonia.py                                       | Sonia  |
| utils.py                                       | N/A (contains util functions)                    |

The classes with methods that are of interest will be EvaluateModel (to evaluate seqs) and SequenceGeneration (to generate seqs), SoniaLeftposRightpos or SoniaLengthPos (to initialise and infer the models) and Plotter (to plot results).

Here is an example usage to infer a human TRB selection model. 
Data and gen files are included in the GitHub repository to demonstrate usage, however we recommend to expand both data and generated files for an accurate inference.

```
import os
from sonia_leftpos_rightpos import SoniaLeftposRightpos
from sonia.evaluate_model import EvaluateModel
from sonia.sequence_generation import SequenceGeneration
from sonia.plotting import Plotter
work_folder = './' # where data files are and output folder should be

data_file = work_folder + 'data_seqs.txt' # file with data sequences
gen_file = work_folder + 'gen_seqs.txt' # file with generated sequences if not generated internally
output_folder = work_folder + 'selection/' # location to save model

# %%
epochs = 30  # maximum epochs to run

# %%  loading lists of sequences with gene specification
with open(data_file) as f: # this assume data sequences are in semi-colon separated text file, with gene specification
    data_seqs = [x.strip().split(';') for x in f]

gen_seqs = []
with open(gen_file) as f:  # this assume generated sequences are in semi-colon separated text file, with gene specification
    gen_seqs = [x.strip().split(';') for x in f]

# creates the model object, load up sequences and set the features to learn
qm = SoniaLeftposRightpos(data_seqs=data_seqs, gen_seqs=gen_seqs)

# %% inferring the model
qm.infer_selection(epochs=epochs)

# %% plot results
pl=Plotter(qm)
pl.plot_model_learning( 'model_learning.png')
pl.plot_vjl(os.path.join('marginals.png')
pl.plot_logQ( 'log_Q.png')

# %% saving the model
if not os.path.isdir(output_folder):
    os.mkdir(output_folder)
qm.save_model(output_folder + 'SONIA_model_example')

# %% load evaluation class
ev=EvaluateModel(sonia_model=qm)
sq=SequenceGeneration(sonia_model=qm)
# generate seqs pre
print(sq.generate_sequences_pre(10))

# %% generate seqs post
seqs= sq.generate_sequences_post(10)
print(seqs)

# %% evaluate Q, pgen and ppost of sequences
qs,pgens,pposts= ev.evaluate_seqs(seqs)
print(pgens)
print(pposts)
print(qs)


```

Additional documentation of the modules is found in their docstrings (accessible either through pydoc or using help() within the python interpreter).

## Notes about CDR3 sequence definition

This code is quite flexible, however it does demand a very consistent definition of CDR3 sequences.

**CHECK THE DEFINITION OF THE CDR3 REGION OF THE SEQUENCES YOU INPUT.** This will likely be the most often problem that occurs.

The default models/genomic data are set up to define the CDR3 region from the conserved cysteine C (INCLUSIVE) in the V region to the conserved F or W (INCLUSIVE) in the J. This corresponds to positions X and X according to IMGT. This can be changed by altering the anchor position files, however the user is strongly recommended against this.

## Contact

Any issues or questions should be addressed to [us](mailto:zachary.sethna@gmail.com,giulioisac@gmail.com).

## License

Free use of SONIA is granted under the terms of the GNU General Public License version 3 (GPLv3).