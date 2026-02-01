# pyvolleydata <img src="https://github.com/ryanndu/pyvolleydata/raw/main/assets/images/pyvolleydata-logo.svg" align="right" width="150" height="150"/>

--- 

## Overview

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pyvolleydata?period=total&units=NONE&left_color=BLACK&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/pyvolleydata)

**[pyvolleydata](https://github.com/ryanndu/pyvolleydata)** is a comprehensive Python package designed for sports analytics. It can be used to access, process, and analyze professional volleyball data.

Currently supports:
- **Major League Volleyball (MLV)**
- **League One Volleyball (LOVB)**
- **Athlete Unlimited Pro Volleyball (AUPVB)**

---

## Installation

Install the latest release via pip:

```bash
$ pip install pyvolleydata
```

---

## Quick Start

Get started by retrieving the player boxscore data for the 2024 MLV season:

```
from pyvolleydata.get_data import load_player_boxscore()

# Load the 2024 MLV season player boxscore
player_boxscore = load_player_boxscore("mlv", 2024)

# Preview the data
print(player_boxscore.head())
```

---

## Contributing

Contributions are welcome!
- **Open an issue** on our **[GitHub Issues](https://github.com/ryanndu/pyvolleydata/issues)** page
- **Email Me** directly at **[ryandu343@gmail.com](mailto:ryandu343@gmail.com)**

---

## License

`pyvolleydata` was created by Ryan Du and David Awosoga. It is licensed under the terms of the MIT license.

---

## Credits

`pyvolleydata` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).

A big thanks to [Rebecca Lai](https://www.rebeccalai.net) for the awesome logo design!