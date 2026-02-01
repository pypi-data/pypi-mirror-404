# must-gather-parser

[![Python Version](https://img.shields.io/pypi/pyversions/must-gather-parser.svg)](https://pypi.org/project/must-gather-parser/)
![publish workflow](https://github.com/gmeghnag/must-gather-parser/actions/workflows/publish.yml/badge.svg) 
![version](https://img.shields.io/pypi/v/must-gather-parser?label=version&color=green)

Asynchronous (multi) must-gather parsing library.

## INSTALL
```
pip install must-gather-parser
```

---

This module uses [**PyYAML**](https://github.com/yaml/pyyaml) for parsing YAML files.

For **significantly better performance**, PyYAML should be installed **with [libyaml](https://github.com/yaml/libyaml) support**.  
When available, PyYAML automatically uses its C-based loader, resulting in much faster YAML processing.

#### `libyaml` installation
```
# Debian / Ubuntu
sudo apt install libyaml-dev
```
```
# macOS
brew install libyaml
```
```
# Fedora
sudo dnf install libyaml-devel
```

## USAGE
```python
import asyncio
from must_gather_parser import MustGather
import json

must_gather = MustGather()

async def main():
    try:
        must_gather.use("/home/must-gather.local.1972254135986597168")
        x = await must_gather.get_resources(resource_kind_plural="pods", group="core", all_namespaces=True)
        print(json.dumps(x))
    except:
        must_gather.close()


if __name__ == "__main__":
    asyncio.run(main())
```
