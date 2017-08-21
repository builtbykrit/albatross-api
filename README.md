## Overview of our development process
I've written up a brief overview of our development process [here](https://docs.google.com/a/krit.it/document/d/1tVv2h91jANQfEQy8y-c4LDUUTwnQZVyq4sQfk0Oac9Y/edit?usp=sharing). Read that first before doing anything else.

## Setup Your Development Environment

1. Install postgres on your machine.
2. Clone this repo.
3. Open terminal and navigate to your local copy of this repo.
4. Get `environment_variables.sh` from Bill and put it in your repo root.
5. Run these commands
```
cd .. && python3 -m venv /path/to/case-status-api/repo
cd /path/to/case-status-api/repo
printf '\nsource /path/to/albatross-api/environment_variables.sh' >> ./bin/activate
source ./bin/activate && cd ..
pip install cached_property
pip install -r requirements.txt
sed -i -e "s#set('.*')#set('=\&;:%+~,*@!()/?[]')#" ./repo/lib/python3.X/site-packages/oauthlib/common.py
```

## Developing and Testing
1. Run `source ./bin/activate` before you start developing or testing.
2. To run the API locally use  `python ./manager.py develop`
3. To run the tests use `python ./manager.py test`

## Notes

If you get `environment_variables.sh:6: = not found` when running `source ./bin/activate`, change all instances of `==` to `=`.
