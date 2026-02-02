# sqlit.nvim

Neovim integration for [sqlit](https://github.com/Maxteabag/sqlit).

## Install

Requires sqlit in your PATH.

### lazy.nvim

```lua
{
  "Maxteabag/sqlit",
  subdir = "extras/nvim",
  opts = {},
}
```

### With options

```lua
{
  "Maxteabag/sqlit",
  subdir = "extras/nvim",
  opts = {
    theme = "dracula",
    keymap = "<leader>D",
    args = "",
  },
}
```

## Usage

`<leader>D` or `:Sqlit`

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `theme` | `"textual-ansi"` | sqlit theme (`nil` for default) |
| `keymap` | `"<leader>D"` | Keymap to open (`false` to disable) |
| `args` | `""` | Extra CLI arguments |
