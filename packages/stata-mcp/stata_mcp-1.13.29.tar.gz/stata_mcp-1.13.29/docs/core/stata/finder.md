# Stata Finder
## How It Works

Since most users install Stata in default locations, we created the StataFinder module to automatically locate Stata executables on your device, allowing for a seamless experience in most cases.

### Detection Flow

1. **Environment Variable Priority**: First checks if the `STATA_CLI` environment variable is set; if set, uses it directly
2. **Automatic Detection**: If no environment variable is set, automatically searches for Stata based on the operating system
3. **Version Selection**: When multiple Stata versions are found, automatically selects the highest priority version

### Platform Differences

- **macOS**: Searches `/usr/local/bin` directory and Stata.app in `/Applications`
- **Windows**: Searches default installation paths (Program Files) and all available drives
- **Linux**: Searches `/usr/local/bin` and its subdirectories containing "stata"

### Version Priority

When multiple Stata versions exist on the system, selection rules are as follows:

1. **Edition Type**: MP > SE > BE > IC > default
2. **Version Number**: Within the same edition type, selects the higher version (e.g., Stata 19 > Stata 18)


## Not Found?
If `uvx stata-mcp --usable` remind you not found your Stata, don't worry. If you are sure about you have Stata on your device, follow the steps bellow to solve it. 

### macOS
1. Open your `Stata.app`, you can find `Stata/MP 19.0` or other similar version at the right of Apple logo, click it. 
2. Then, click `install terminal utility`. 
3. Now, you can close Stata, and run `uvx stata-mcp --usable` again. 
4. If there is still `not found`, you can open your `terminal` and run `which stata-mp` (or if your version is StataSE or StataBE, you can relace `stata-mp` with `stata-se` or `stata-be`). 
5. Set environment variable `STATA_CLI` to the path you got from step 4.

for example: 
```bash
sepinetam@sepine-macbook ~ % which stata-mp
/usr/local/bin/stata-mp
sepinetam@sepine-macbook ~ % export STATA_CLI="/usr/local/bin/stata-mp"
sepinetam@sepine-macbook ~ % uvx stata-mcp --usable

===== Stata MCP Configuration Check =====

Operating system (Current: macOS): ✅ PASSED
Python version (Current: 3.13.5): ✅ PASSED
MCP library installation: ✅ PASSED
Locating Stata CLI...
Stata CLI (Path: /usr/local/bin/stata-mp): ✅ PASSED
Testing Stata execution...
Stata execution test: ✅ PASSED

Checking required directories...
Base Dir (Path: /Users/sepinetam/Documents/stata-mcp-folder): ✅ PASSED
Log Dir (Path: /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log): ✅ PASSED
Dofile Dir (Path: /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile): ✅ PASSED
Result Dir (Path: /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-result): ✅ PASSED

===== Summary =====

✅ Success! Your Stata-MCP setup is ready to use.
You can now use Stata-MCP with your preferred MCP client (Claude, Cherry Studio, etc.)
```

More over, write the config into `~/.zshrc` like this:
```bash
cat >> ~/.zshrc <<'EOF'
# Stata CLI path
export STATA_CLI="$(command -v stata-mp 2>/dev/null)"
EOF

source ~/.zshrc
echo "$STATA_CLI"
```

### Linux
1. If you're using a Linux machine without a GUI, you should know where your `stata-mp` executable is located, and I'll assume you're an experienced computer user.
2. Simply set the environment variable `STATA_CLI` to your `stata-mp` executable path, then run `uvx stata-mcp --usable` again. If there are no errors, the configuration is successful.

### Windows
Windows configuration is relatively more complex, but the core approach is similar to macOS and Linux. You need to find your `Stata.exe` (or similarly named) file, then set the `Stata.exe` path to the environment variable `STATA_CLI`. There are many online resources about how to set environment variables in Windows, so you can search for that yourself. Here's how to find the actual `Stata.exe` file:
1. Press the Windows key on your keyboard, search for "Stata", and find the Stata you're using.
2. Right-click and select "Open file location". At this point, there will usually be only two files in this directory - these are not the actual executable files. Right-click and select "Open file location again" to find the real executable file, then set its path to the environment variable `STATA_CLI`.
3. Run `uvx stata-mcp --usable` again. If there are no errors, the configuration is successful.


