local M = {}

M.config = {
  theme = "textual-ansi",
  keymap = "<leader>D",
  desc = "Database (sqlit)",
  args = "",
}

local function build_cmd()
  local cmd = "sqlit"
  if M.config.theme then
    cmd = cmd .. " --theme " .. M.config.theme
  end
  if M.config.args and M.config.args ~= "" then
    cmd = cmd .. " " .. M.config.args
  end
  return cmd
end

function M.open()
  local cmd = build_cmd()

  local ok, snacks = pcall(require, "snacks")
  if ok and snacks.terminal then
    snacks.terminal(cmd)
    return
  end

  local tok, toggleterm = pcall(require, "toggleterm.terminal")
  if tok then
    local Terminal = toggleterm.Terminal
    local sqlit = Terminal:new({
      cmd = cmd,
      direction = "float",
      hidden = true,
      on_open = function()
        vim.cmd("startinsert!")
      end,
    })
    sqlit:toggle()
    return
  end

  vim.cmd("tabnew | terminal " .. cmd)
  vim.cmd("startinsert")
end

function M.setup(opts)
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})

  if M.config.keymap then
    vim.keymap.set("n", M.config.keymap, function()
      M.open()
    end, { desc = M.config.desc })
  end
end

return M
