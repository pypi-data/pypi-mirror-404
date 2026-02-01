# `bebms`

This repository contains the package codes for the ML4H (2025) submission of *Bayesian Event-Based Model for Disease Subtype and Stage Inference*.

## Cite this paper or package 

```
@inproceedings{Hao2025JointProgression,
  author    = {Hongtao Hao and Joseph L. Austerweil},
  title     = {Bayesian Event-Based Model for Disease Subtype and Stage Inference},
  booktitle = {Proceedings of the 5th Machine Learning for Health Symposium},
  volume    = {297},
  pages     = {??--??}, % Page numbers are not provided now, will add later. 
  year      = {2025},
  publisher = {PMLR},
}
```

## Installation

```bash
pip install bebms
```

or git clone this project, and then

```bash
pip install -e .
```

## Generate synthetic data

If you need quick examples of data usable for `bebms` for testing purposes, you can use sample data available at [`bebms/data/samples`](bebms/data/samples/).

If you need to generate synthetic data: Git clone this repository, and at the root, run

```bash
bash gen.sh
```
The generated data will be found at [`bebms/test/my_data`](bebms/test/my_data/) as `.csv` files. 

The parameters are pre-set and can be found at [`bebms/data/params.json`](bebms/data/params.json). You can modify the parameters by modifying the `json` file. 

You can also change parameters in `config.toml` to adjust what data to generate.

### How to understand TURE_ORDERINGS

You'll see "TURE_ORDERINGS" in `true_order_and_stages.json`. How to understand it?

First you get a sorted list of all biomarker names (ascending), call it `list1`. Then you have several true orderings, and we call each ordering `list2`. 

list2[i] = the position (0-indexed) of biomarker list1[i] in the true ordering. 

### Details

You can look into the [`gen.py`](bebms/test/gen.py) and [`generate_data.py`](bebms/generate_data.py) for more details. By default, `keep_all_cols = False` and the result is the data in wide format. 

You can change it to `keep_all_cols = False`, and the data will be in long (tidy) format. This is because the wide format cannot contain the `affected` column which is regarding to biomarker, rather than each participant. 

## Run `bebms` algorithm 

After git cloning this repository and generating syntheti cdata, to run `bebms`, at the root, run 

```bash
bash test.sh
```

You can check [`bebms/test/test.py`](bebms/test/test.py) to learn how to use the [`run_bebms`](bebms/run.py) function. 

The results will be saved in the folder of [`bebms/test/algo_results`](bebms/test/algo_results/).

### Compare with SuStaIn

You can also compare the results of `bebms` with those of SuStaIn.

First, you need to install packages required by SuStaIn:

```bash
pip install git+https://github.com/noxtoby/awkde
pip install git+https://github.com/hongtaoh/ucl_kde_ebm
pip install git+https://github.com/hongtaoh/pySuStaIn
```

Then, at the root of this repository, run 

```bash
bash test_sustain.sh
```

You can check details at [`bebms/test/test_sustain.py`](bebms/test/test_sustain.py).

The results will be saved in the folder of [`bebms/test/sustain_results`](bebms/test/sustain_results/).

### Save comparison results

You can save the results of `bebms` along with those of SuStaIn by running at the root:

```bash
python3 save_csv.py
```

The results will be found at the root as `all_results.csv`. 

## Use your own data

You can use your own data. But make sure that your data follows the format as in data in [`bebms/data/samples`](bebms/data/samples/).

### Find the optimal number of subtypes

After you have your own data, the first step is to find the optimal number of subtypes. 

```py
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from bebms.cross_validate import cross_validatation
import bebms.utils as utils

data_file = 'path/to/your/data.csv'

cvic_scores, optimal_n = cross_validatation(
    data_file=data_file,
    iterations=10000, # how many MCMC iterations to run. 
    n_shuffle=2, # how many biomarkers to shuffle in each subtype; recommend 2.
    n_subtype_shuffle=2, # how many subtypes to shuffle; recommend 2.
    burn_in=200, 
    prior_n=1, # Strength of the prior belief in prior estimate of the mean (μ), set to 1 as default
    prior_v=1, # # Prior degrees of freedom, influencing the certainty of prior estimate of the variance (σ²), set to 1 as default
    max_n_subtypes=6, # the max number of subtypes
    N_FOLDS=5, # K-fold validation. Choose K here. 
    seed=42, # random seed. 
    with_labels=True, # whether to assume the knowledge of diagnosis labels, i.e., healthy or not. 
    z_score_norm=False # whether to use z score normalization for all biomarker data. default is false
)

# to get the optimal number of subtypes
ml_n_subtypes = utils.choose_optimal_subtypes(cvic_scores)
print(ml_n_subtypes)

# Summarize results
df_cvic = pd.DataFrame({
    "n_subtypes": np.arange(1, 7),
    "CVIC": cvic_scores
})
print(df_cvic)

# Plot CVIC curve
plt.figure(figsize=(6,4))
plt.plot(df_cvic["n_subtypes"], df_cvic["CVIC"], marker="o")
plt.xlabel("Number of subtypes")
plt.ylabel("CVIC (lower is better)")
plt.title("Cross-validated model selection (BEBMS)")
plt.grid(True)
plt.show()
```

### Run BEBMS

After you know the optimal number of subtypes, you can start running `bebms` on your dataset. 

It's ideal if you can try different random seeds and see which one leads to the highest data log likelihood:

```py
import pandas as pd 
import numpy as np 
from bebms import cross_validatation, run_bebms
from collections import defaultdict, Counter

data_file = 'path/to/your/data.csv'

dic = defaultdict(float)
for _ in range(10): # try 10 random seeds; modify the number as you wish. 
    x = np.random.randint(1, 2**32 - 1)
    results = run_bebms(
        data_file= data_file,
        n_subtypes=3, # that is the optimal number of subtypes you identified above
        output_dir='bebms_results',
        n_iter=20000, # number of MCMC iterations.
        n_shuffle=2, 
        n_subtype_shuffle=2,
        burn_in=200,
        thinning=1,
        seed = x, 
        obtain_results=True, # to get the results
        save_results=False, # but no need to save the results; why? because here we only need to get the data likelihood, and no need to save the results
        with_labels=True, # we assume the knowledge of diagnosis labels
        save_plots=False, # we do not save plots
        z_score_norm=False # whether to use z score normalization for all biomarker data. default is false
    )
    dic[x] = results['max_log_likelihood']

# By checking dic, you can know which random seed led to the highest data log likelihood

# Finally, you can run bebms to get the results. 
seed = 12345 # Suppose that is the optimal seed you identified above

results, all_orders, all_loglikes, best_order_matrix, biomarker_names, ml_stage, ml_subtype = run_bebms(
        data_file= data_file,
        n_subtypes=3,
        output_dir='bebms_results', # where results will be saved into
        n_iter=20000,
        n_shuffle=2,
        n_subtype_shuffle=2,
        burn_in=200,
        thinning=1,
        seed = seed,
        obtain_results=True,
        save_results=True, # Now we need to save results
        with_labels=True,
        save_plots=True # Now we need save the result plots. 
    )
```

### Z score normalization

The default of the functions of `run_bebms` and `cross_validation` is `z_score_norm = False`. But you can try `z_score_norm = True` and see which results are more plausible. This might require domain expertise. 


## Changelogs

- 2025-08-21 (V 0.0.3)
    - Did the `generate_data.py`.
- 2025-08-22 (V 0.0.5)
    - Did the `mh.py`
    - Correct conjugate_priors implementation.
- 2025-08-23 (V 0.1.2)
    - Improved functions in `utils.py`.
- 2025-08-29 (V 0.1.3)
    - Didn't change much. 
- 2025-08-30 (V 0.1.8)
    - Optimized `compute_likelihood_and_posteriors` such that we only calculate healthy participants' ln likelihood once every time. 
    - Made sure subtype assignment accuracy does not apply to healthy participants at all. 
    - Fixed a major bug in data generation. The very low subtype assignment might be due to this error.
    - Included both subtype accuracy in `run.py`. 
- 2025-08-31 (V 0.2.5)
    - Resacle event times and disease stages for exp7-9 such that max(event_times) = max_stage -1, and max(disease_stages) = max_stage. 
    - Changed the experiments and some of the implementation. 
    - Forcing `max(event_times) = max_stage -1`, but not forcing disease stages. 
- 2025-09-01 (V 0.2.9)
    - REMOVED THE Forcing `max(event_times) = max_stage -1`
    - Modified the `run.py`.
- 2025-09-02 (V 0.3.3.1)
    - Redid the staging and subtyping. 
    - Integrated with labels and not. 
- 2025-09-04 (V 0.3.3.2)
    - Made sure in staging with labels, the new_order indices starts from 1 instead of 0. This is because participant stages now start from 0.
- 2025-09-06 (V 0.3.5.6)
    - Added the plot function back.
- 2025-09-08 (V 0.3.5.8)
    - Added `ml_subtype` in output results. 
    - Added all_logs to the output returned in `run.py`.
- 2025-09-21 (V 0.3.9)
    - Removed `iteration >= burn_in` when updating best_*. 
- 2025-11-03 (V 0.4.1)
    - Changed the package name to `bebms`. 
    - Edited README. 
- 2025-11-06 (V 0.4.3)
    - Updated README. 
    - Allowed `keep_all_cols=True` when generating synthetic data. Will use the long format in that situation. 
- 2025-11-07 (V 0.4.5)
    - Now `z_score_norm` is added in `run.py` and `cross_validation.py` to allow users to do z score normalization for the data matrix.
- 2026-01-21 (V 0.4.8)
    - Now include `pyyaml` in dependences. 
    - Fix the bug of stage assignemnt 
  - Before
  
```py
  # assign NEW consecutive participant ids
old_unique = pd.unique(df['participant'])
new_ids = np.arange(new_participant_start, new_participant_start + len(dff))
old_to_new = dict(zip(old_unique, new_ids))
dff['participant'] = dff['participant'].map(old_to_new)  # ← 先转换成 NEW IDs

# --- Assign stage + subtype correctly (works for both formats!) ---
stage_map = dict(zip(df['participant'].unique(), subtype_dict[filename]['true_stages']))
dff['stage_assignments'] = dff['participant'].map(stage_map)  # ← 用 NEW IDs 去 map OLD IDs！❌
dff['subtype_assignments'] = subtype_idx
```

This will cause some NaN in stage assignments in `true_order_and_stages.json`. But this won't change our results because we do not use stage assignments in our training or testing. 

Changed to correct:

```py
# assign NEW consecutive participant ids
old_unique = pd.unique(df['participant'])
# --- Assign stage + subtype correctly (works for both formats!) ---
stage_map = dict(zip(df['participant'].unique(), subtype_dict[filename]['true_stages']))
dff['stage_assignments'] = dff['participant'].map(stage_map)  # ← 用 OLD IDs 去 map OLD IDs ✓
dff['subtype_assignments'] = subtype_idx
new_ids = np.arange(new_participant_start, new_participant_start + len(dff))
old_to_new = dict(zip(old_unique, new_ids))
dff['participant'] = dff['participant'].map(old_to_new)  # ← 然后转换成 NEW IDs ✓
```


- 2026-01-27 (V 0.5.0)
  - Added the default theta phi to `mh.py`. It was already in `run.py`. 
  
- 2026-01-31 (V 0.6.0)
- 
### Fixed
- **Bug fix in `xi` experiments for subtype data generation**: Event times generated from Beta distribution are now sorted before assignment to biomarkers. Previously, when `fixed_biomarker_order=True`, random (unsorted) Beta-sampled event times were assigned to biomarkers, causing the true ordering to be determined by these random values rather than the intended subtype ranking. This affected experiments `xiNearNormal_kjContinuousBeta_sigmoid` and `xiNearNormal_kjContinuousBeta_xnjNormal`.