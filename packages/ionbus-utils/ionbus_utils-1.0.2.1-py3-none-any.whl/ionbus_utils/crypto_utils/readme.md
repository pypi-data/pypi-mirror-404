# Crypto Utilities

<!-- TOC start (generated with https://bitdowntoc.derlin.ch/) -->

- [Overview](#overview)
- [Creating Encryption Hash](#creating-encryption-hash)
   * [Important](#important)
- [Creating Authentication YAML files](#creating-authentication-yaml-files)
- [Accessing authentication YAML files](#accessing-authentication-yaml-files)
   * [Setup Environment Variables](#setup-environment-variables)
   * [To access in Python](#to-access-in-python)
   * [To access as a PDYaml object](#to-access-as-a-pdyaml-object)

<!-- TOC end -->


## Overview

The `crypto_utils` directory contains utilities for cryptographic operations and authentication management. These utilities are designed to handle encryption, decryption, key management, and the creation of authentication files.

## Creating Encryption Hash

Before doing anything else, you need to create and store a random 128 bit key for encrypting and decrypting passwords.

Everybody who uses this will have (at least) a `"personal"` key.  If you work with service accounts, you may also have additional keys.

To generate a key:

```bash
# to generate a personal key
python -m ionbus_utils.crypto_utils.auth_utils --generate

# To generate a key named `oxford`
python -m ionbus_utils.crypto_utils.auth_utils --generate --key-name oxford
```


When running this command, you will then see it output new value for `IBU_AESGCM` environment variable.

On windows you can copy and paste the `setx` command it writes and run it.  On linux, you will want to past the `export` command into your `.bash_profile` file in your home directory.

```bash
(py_39_pd15_20250604) C:\Users\cplager\LocalCode> python -m ionbus_utils.crypto_utils.auth_utils --generate --key_name oxford
2025-06-04 13:24:32.759 INFO     [crypto_utils        :generate_key         (  26)] Set IBU_AESGCM environment variable to personal:this_is_secret==;oxford:this_is_too==
You can run in command prompt
setx IBU_AESGCM personal:this_is_secret==;oxford:this_is_too==
```

### Important
On windows, when you run the `setx` command, it sets the user environment variable permanently, but it does **not** set it in the terminal window that ran the job. 

After setting this variable, you will need to completely close and restart **all** of your IDE (VSCode, pycharm, etc) windows (**File** -> **eXit**) and then restart in order to pick up the change..

## Creating Authentication YAML files

We use `ionbus_utils.crypto_utils.auth_utils` for creating and updating the password of authentication YAML files.

Files are stored in linux home directory by default (`w:\home\cplager` for `cplager`).  A full path can be given to have it store elsewhere by providing an absolute path.

Some examples below:

```bash
# Create an authentication file
python -m ionbus_utils.crypto_utils.auth_utils --create

# Create an authentication file that has additional parameters added
# `model_number` = 2 and `model_name` = `"rover"`

python -m ionbus_utils.crypto_utils.auth_utils --create --json "{\"model_number\":2,\"model_name\":\"rover\"}"  some_auth.yaml
```

## Accessing authentication YAML files

### Setup Environment Variables

In general, we can tell the code to use YAML files by storing the full locations of the files in an environment variable.  In ionbus_utils, this information is stored in `IBU_AUTH_FILES` environment variable.

For example, if you want two configurations `prod` and `dev` set  `IBU_AUTH_FILES` to: 

```bash
prod::/home/someuser/prod_auth.yaml;dev::/home/someuser/dev_auth.yaml
```

The environment variable is setup as a collection of key value pairs.

The key and the value are separated by double colon (`::`); each pair is separated by semi-colon (`;`).  The above string is equivalent to:

```python
{
    "prod" : r"/home/someuser/prod_auth.yaml",
    "dev" : r"/home/someuser/dev_auth.yaml",
}
```

### To access in Python

Below are some different code snippets.  `cred` will contain `username`, decrypted `password` and whatever else is in YAML file.

``` python
from ionbus_utils.crypto_utils.auth_utils import get_auth_credentials

# Get 'dev' credentials using `IBU_AUTH_FILES` environment variable
cred = get_auth_credentials("dev", env_name="IBU_AUTH_FILES")

# get default (first) credentials in `SOME_OTHER_NAME` environment variable
cred = get_auth_credentials(env_name="SOME_OTHER_NAME")
```

### To access as a PDYaml object

If you have a `PDYaml` subclass for your credentials, you can use `get_auth_credentials_pdyaml` to get a typed object instead of a dictionary.

``` python
from ionbus_utils.crypto_utils.auth_utils import get_auth_credentials_pdyaml
from ionbus_utils.yaml_utils import PDYaml

class MyAuthConfig(PDYaml):
    username: str
    password: str
    name: str
    # add any additional fields from your YAML file

# Get 'prod' credentials as a MyAuthConfig instance
config = get_auth_credentials_pdyaml(MyAuthConfig, "prod", env_name="IBU_AUTH_FILES")

# Access fields with type safety
print(config.username)
print(config.password)
```
