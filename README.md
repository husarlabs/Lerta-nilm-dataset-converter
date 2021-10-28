## About The Project

This repository contains basic data cleaning steps.
In order to find more information about dataset please check at [https://dataset_url.com](https://example.com)

We aimed at providing compatibility with the [NILMTK](https://github.com/nilmtk/nilmtk) repository to make this data as useful as possible. 
These cleanup steps are required to obtain a CLEAN version of the dataset that can be successfully used in the NILM repository. 
Our converter can be found in the NILMTK repository under the name `lerta_converter`.

The result is a pandas.Dataframe with 6s sampling saved as .csv file.
A clean dataframe includes a of columns with an aggregated and individual device signal.

## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

* You need python to run the code. We used python 3.8 version.
* You need to download and unpack the [RAW](https://example.com) data.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/husarlabs/nilm-dataset-converter
   ```
3. Install packages
   ```sh
   pip install requirements.txt
   ```


## Usage

1. Run code
   ```sh
   python main.py -d <directory_with_raw>
   ```
