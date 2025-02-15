# Example Regex Engine

Use `poetry` to create a virtualenv and download all dependencies:

```
pip install poetry
poetry shell
python main.py
```

You can use your own regular expression and test strings:
```
# Matches
python main.py "(0a|b)" "0a"

# Doesn't match
python main.py "(0a|b)" "0b"
```

The alphabet defaults to "0ab"
