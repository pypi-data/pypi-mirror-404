vim.api.nvim_create_user_command("Sqlit", function()
  require("sqlit").open()
end, { desc = "Open sqlit" })
