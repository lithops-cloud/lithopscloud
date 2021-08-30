# Tool to generate Lithops configuration file

Lithopscloud is a CLI tool that greatly simplifies user experience to generate Lithops and Ray configuration file.

## Setup

Install `lithopscloud` from pip repository

        pip install lithopscloud

Use your existing IBM Cloud an API key or generate new API Key as described [here](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)

## Usage
Use tool as follows

```
lithopscloud --iam-api-key IAM_API_KEY --format lithops --output-file lithops_config.yaml
```
Configure Lithops to use generated configuration file

```
export LITHOPS_CONFIG_FILE=lithops_config.yaml
```

Current version supports Lithops with IBM COS and Gen2 backend. It also supports Ray-Gen2 configuration.

## How to add new unsupported sections to config file


### If the new configuration is provider specific

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface
2. add your implementation under __provider__ package
3. add reference to your implementation in the list of exported modules, e.g. [lithops modules](src/lithopscloud/modules/lithops/__init__.py__)


### If the new configuration is common for multiple providers

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface to hold common logic
2. add your implementation to __modules__ package
3. extend your common implementation under each provider package, e.g. [lithops image.py](src/lithopscloud/modules/lithops/image.py) and [ray image.py](src/lithopscloud/modules/ray/image.py) to have config file specific logic
