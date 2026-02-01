# basic-shit

**Finding your project root in Python. You know, basic shit.**

[![PyPI version](https://badge.fury.io/py/basic-shit.svg)](https://badge.fury.io/py/basic-shit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Because apparently in 2026, Python still can't do this out of the box.

## The Problem

You want to find your project root. Should be easy, right? **WRONG.**

Python has been around since 1991 and still doesn't have a built-in way to find your project root directory. 

Want to access a file in your project? Better hope you started your script from the right directory. Or write 50 lines of `os.path` spaghetti. Or use `__file__` with a bunch of `.parent.parent.parent` calls that break when you refactor.

It's 2026. This is **basic shit**.

## The Solution

```python
from basic_shit import get_project_root

root = get_project_root()
That's it. That's the whole library.

Installation
bash
pip install basic-shit
Usage
Basic Usage
python
from basic_shit import get_project_root

# Get your project root
root = get_project_root()

# Now use it
data_dir = root / "data"
config_file = root / "config.yaml"
How It Works
basic-shit walks up the directory tree from your current file and looks for marker files that indicate the project root:

.project_root (recommended - create this in your project root)

.git

pyproject.toml

requirements.txt

setup.py

Custom Markers
python
from basic_shit import get_project_root

# Use your own marker files
root = get_project_root(marker_files=(".mymarker", "package.json"))
The Recommended Way
Create a .project_root file in your project root:

bash
touch .project_root
Now basic-shit will find it instantly. No ambiguity. No magic. Just basic shit that works.

Why This Exists
Because I got tired of:

❌ os.path.dirname(os.path.abspath(__file__)) spaghetti

❌ Hardcoded ../../.. paths that break when you refactor

❌ os.getcwd() that depends on where you run the script from

❌ Different behavior in development vs. production

❌ Writing the same "find project root" function in every project

Why The Name?
Because finding your project root IS basic shit. And Python making it this hard is ridiculous.

Requirements
Python 3.8+

That's it. No dependencies. Because it's basic shit.

License
MIT License - because even licensing shouldn't be complicated.

Contributing
Found a bug? Have an idea? PRs welcome!

Just remember: keep it simple. This library does one thing and does it well. If your PR adds 500 lines of code, you missed the point.

Acknowledgments
Inspired by every developer who ever screamed "WHY ISN'T THIS BUILT-IN?!" at their computer.

You're not alone. We've all been there.

basic-shit - Solving Python's hardest problem since 1991. 🎯