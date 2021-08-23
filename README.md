# lithopscloud provides convinient way to generate configuration files

> Use of python virtual environment, e.g. [virtualenv](https://virtualenv.pypa.io/en/latest) is greatly encouraged, to avoid installing Python packages globally which could break system tools or other projects

Install from pip `pip install lithopscloud`

Current version supports basic lithops and ray gen2 provider confguration.

.
├── LICENSE
├── README.md
└── src
    └── lithopscloud
        ├── \_\_init__.py
        ├── __config_builder.py__
        ├── main.py
        └── modules
            ├── \_\_init__.py
            ├── endpoint.py
            ├── image.py
            ├── ssh_key.py
            ├── utils.py
            ├── vpc.py
            ├── lithops
            │   ├── \_\_init__.py
            │   ├── endpoint.py
            │   ├── image.py
            │   ├── defaults.yaml
            │   ├── ssh_key.py
            │   └── vpc.py
            └── ray
                ├── \_\_init__.py
                ├── endpoint.py
                ├── floating_ip.py
                ├── image.py
                ├── defaults.yaml
                ├── ssh_key.py
                ├── vpc.py
                └── workers.py

# Need to add new unsupported sections to config file? No problem. The framework is easily extendable with new configurations

## If the new configuration is provider uniqueue, e.g. [floating_ip.py](src/lithopscloud/modules/ray/floating_ip.py):

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface
2. add your implementation under provider package
3. add referencce to your implementation in the list of exported modules, e.g. [lithops modules](src/lithopscloud/modules/lithops/__init__.py__)


## If the new configuration is common for multiple providers, e.g. [image.py](src/lithopscloud/modules/image.py):

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface to hold common logic
2. add your implementation to modules package
3. extend your common implementation under each provider package, e.g. [lithops image.py](src/lithopscloud/modules/lithops/image.py) and [ray image.py](src/lithopscloud/modules/ray/image.py) to have config file specific logic