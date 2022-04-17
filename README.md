# Tool to generate Lithops configuration file

Lithopscloud is a CLI tool that greatly simplifies user experience by generating Lithops and Ray configuration files.

## Setup

The tool been mostly tested with Ubuntu 18.04/20.04, but should work with most Linux systems
Requirements: `ssh-keygen` utility installed:
```
sudo apt install openssh-client
```

Install `lithopscloud` from pip repository

```
pip install lithopscloud
```

## Usage
Use the configuration tool as follows

```
lithopscloud [--iam-api-key IAM_API_KEY] [-i INPUT_FILE] [-o OUTPUT_PATH] [--verify_config CONFIG_FILE_PATH] [--version]
```
Get a short description of the available flags via ```lithopscloud --help```

<br/>

#### Flags Detailed Description

<!--- <img width=125/> is used in the following table to create spacing --->
 |<span style="color:orange">Key|<span style="color:orange">Default|<span style="color:orange">Mandatory|<span style="color:orange">Additional info|
 |---|---|---|---|
 | iam-api-key   | |yes|IBM Cloud API key. To generate a new API Key, adhere to the following [guide](https://www.ibm.com/docs/en/spectrumvirtualizecl/8.1.3?topic=installing-creating-api-key)
 | input-file    |<compute_backend>/defaults.py| no | Existing config file to be used as a template in the configuration process |
 | output-path   |A randomly generated path to a randomly named yaml file | no |A custom location the config file will be written to |
 | verify-config <img width=125/>| | no |Verifies the integrity of an existing config file and outputs a usable config file based on it. Currently doesn't support gen2 backends. 
 | version       | | no |Returns lithopscloud's package version|

<br/>

#### Verify Additional ways of configuration
Using the ```verify-config``` option enables verification of additional valid ways of configuration, that otherwise 
left unchecked. This mode scans for any possible subset of valid parameters and extract them to output a new 
lithops config file (e.g., verify cos configured by HMAC credentials).
To utilize simply run ```lithopscloud --verify-config CONFIG_FILE_PATH -o OUTPUT_FILE_PATH```
<br/> Please note that this feature doesn't currently support the verification of gen2 backends. 

## Supported backends:
<table>
<tr>
<th align="center">
<p>
<span style="color:orange">Standalone Compute Backends</span> 
</p>
</th>
<th align="center">

<p>
<span style="color:orange">Serverless Compute Backends</span> 
</p>
</th>
<th align="center">
<p>
<span style="color:orange">Storage Backends</span> 
</p>
</th>
</tr>
<tr>
<td>

- Gen2/Lithops
- Gen2/Ray
- Local Host

</td>
<td>

- IBM Cloud Functions
- IBM Code Engine
</td>
<td>

- IBM Cloud Object Storage

</td>
</tr>
</table>

### Using lithopscloud config tool programmatically
Notice, not all fields are mandatory. Unspecified resources will be created automatically on the backend.

E.g.
If existing vpc id not provided - vpc will be created automatically with all required peripherial resources like security groups, gateway.. etc following minimal default requierments
If ssh key details not provided - new ssh key pair will be generated and registered in ibm cloud

##### Lithops Gen2
```
from lithopscloud import generate_config
from lithopscloud import LITHOPS_GEN2, LITHOPS_CF, LITHOPS_CE, RAY_GEN2, LOCAL_HOST

api_key = '<IAM_API_KEY>'
region = 'eu-de'
generate_config(LITHOPS_GEN2, api_key, region, cos_bucket_name='kpavel-bucket', image_id='r010-5a674db7-95aa-45c5-a2f1-a6aa9d7e93ad', key_id='r010-fe6cb103-60e6-46bc-9cb5-14e415990849', ssh_key_filename='/home/kpavel/.ssh/id_rsa', profile_name='bx2-2x8', vpc_id='r010-af1adda4-e4e5-4060-9aa2-7a0c981aff8e')

```

Mandatory fields are: backend_type (LITHOPS_GEN2), api_key, region and cos_bucket.
Minimal example:

```
from lithopscloud import generate_config
from lithopscloud import LITHOPS_GEN2, RAY_GEN2

api_key = <IAM_API_KEY>
region = 'ca-tor'
cos_bucket_name='kpavel-bucket'
config_file = generate_config(LITHOPS_GEN2, api_key, region, cos_bucket_name=cos_bucket_name)
```

###### Ray Gen2
```
from lithopscloud import generate_config
from lithopscloud import RAY_GEN2

api_key = '<IAM_API_KEY>'
region = 'eu-de'
generate_config(RAY_GEN2, api_key, region, image_id='r010-5a674db7-95aa-45c5-a2f1-a6aa9d7e93ad', key_id='r010-fe6cb103-60e6-46bc-9cb5-14e415990849', ssh_key_filename='/home/kpavel/.ssh/id_rsa', profile_name='bx2-2x8', vpc_id='r010-af1adda4-e4e5-4060-9aa2-7a0c981aff8e', min_workers=1, max_workers=1)
```

Mandatory fields are: backend_type (LITHOPS_GEN2), api_key, region and cos_bucket.
Minimal example:

```
from lithopscloud import generate_config
from lithopscloud import RAY_GEN2

api_key = <IAM_API_KEY>
region = 'eu-de'
config_file = generate_config(RAY_GEN2, api_key, region)
```

## For Contributors

### Add new unsupported sections to config file

#### If the new configuration is provider specific

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface
2. add your implementation under __provider__ package
3. add reference to your implementation in the list of exported modules, e.g. [lithops modules](src/lithopscloud/modules/lithops/__init__.py__)


#### If the new configuration is common for multiple providers

1. implement [__config_builder.py__](src/lithopscloud/modules/config_builder.py) interface to hold common logic
2. add your implementation to __modules__ package
3. extend your common implementation under each provider package, e.g. [lithops image.py](src/lithopscloud/modules/lithops/image.py) and [ray image.py](src/lithopscloud/modules/ray/image.py) to have config file specific logic
