# 🔖 Bkmrks v0.4.1

🔖 Bkmrks helps you to manage your bookmarks.

## Installation

You can install directly in your `pip`:
```shell
pip install bkmrks
```

I recomend to use the [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), so you can just use the command bellow and everything is installed:
```shell
uv add bkmrks
uv run bkmrks --version
```

But you can use everything as a tool, for example:
```shell
uvx bkmrks --version
```

## How to use

You can start just rendering your first bookmarks page with:
```shell
bkmrks render
```
That will create your rendered homepage at the `public` folder.

Edit the `bookmarks/index.yaml` file with your own bookmarks.
The `yaml` file has the first node to `lines` and the second node for `urls`.

You can modify the template in the template folder.

That's the basic usage!
But you can understand more using the help:
```shell
bkmrks --help
```

## See Also

- Github: https://github.com/bouli/bkmrks
- PyPI: https://pypi.org/project/bkmrks/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
