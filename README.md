# lithopscloud provides convinient way to generate configuration files

> Use of python virtual environment, e.g. [virtualenv](https://virtualenv.pypa.io/en/latest) is greatly encouraged, to avoid installing Python packages globally which could break system tools or other projects

Install from pip `pip install lithopscloud`

[Generate API KEY](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)

Run example
```
lithopscloud --iam-api-key IAM_API_KEY --format lithops --output-file lithops_config.yaml
export LITHOPS_CONFIG_FILE=lithops_config.yaml
```

Current version supports basic lithops and ray gen2 provider confguration.

```
.
├── LICENSE
├── README.md
└── src
    └── lithopscloud
        ├── __init__.py
        ├── __config_builder.py__
        ├── main.py
        └── modules
            ├── __init__.py
            ├── endpoint.py
            ├── image.py
            ├── ssh_key.py
            ├── utils.py
            ├── vpc.py
            ├── lithops
            │   ├── __init__.py
            │   ├── endpoint.py
            │   ├── image.py
            │   ├── defaults.yaml
            │   ├── ssh_key.py
            │   └── vpc.py
            └── ray
                ├── __init__.py
                ├── endpoint.py
                ├── floating_ip.py
                ├── image.py
                ├── defaults.yaml
                ├── ssh_key.py
                ├── vpc.py
                └── workers.py
```

# Need to add new unsupported sections to config file?


## If the new configuration is provider uniqueue, e.g. [floating_ip.py](src/lithopscloud/modules/ray/floating_ip.py):

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface
2. add your implementation under __provider__ package
3. add reference to your implementation in the list of exported modules, e.g. [lithops modules](src/lithopscloud/modules/lithops/__init__.py__)


## If the new configuration is common for multiple providers, e.g. [image.py](src/lithopscloud/modules/image.py):

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface to hold common logic
2. add your implementation to __modules__ package
3. extend your common implementation under each provider package, e.g. [lithops image.py](src/lithopscloud/modules/lithops/image.py) and [ray image.py](src/lithopscloud/modules/ray/image.py) to have config file specific logic
