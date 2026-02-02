# Publishing GemCLI to PyPI 🚀

Complete guide to publish GemCLI as an official Python package that anyone can install.

---

## 📋 Quick Start (For First-Time Publishers)

### Step 1: Create PyPI Account

1. Go to **https://pypi.org/account/register/**
2. Verify your email address
3. Set up 2FA (Two-Factor Authentication) - **Required**
4. Save your recovery codes!

### Step 2: Install Build Tools

```bash
pip install --upgrade build twine
```

### Step 3: Build the Package

```bash
# Navigate to your project directory
cd D:\CliTool

# Build distribution packages
python -m build
```

This creates in `dist/`:
- `gemcli-1.0.0-py3-none-any.whl` (wheel file)
- `gemcli-1.0.0.tar.gz` (source distribution)

### Step 4: Test on Test PyPI (Recommended)

```bash
# Upload to Test PyPI first
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your Test PyPI token>
```

**Create Test PyPI Token:**
- Go to https://test.pypi.org/manage/account/token/
- Click "Add API token"
- Name it "GemCLI Upload"
- Copy the token (starts with `pypi-`)

**Test Installation:**
```bash
pip install --index-url https://test.pypi.org/simple/ gemcli

# Test the command
gem start
```

### Step 5: Upload to Real PyPI 🎉

```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your PyPI token>
```

**Create PyPI Token:**
- Go to https://pypi.org/manage/account/token/
- Click "Add API token"
- Name it "GemCLI Upload"
- Copy the token and save it securely

### Step 6: Celebrate! 🎊

Your package is now live! Anyone can install it:

```bash
pip install gemcli
gem start
```

---

## 🔐 Using API Tokens (Recommended)

Create a `.pypirc` file in your home directory for easier uploads:

**Windows:** `C:\Users\YourName\.pypirc`
**Mac/Linux:** `~/.pypirc`

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YourActualTokenHere

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YourTestTokenHere
```

Now you can upload without typing credentials:
```bash
python -m twine upload dist/*
```

---

## 📦 Installation Methods for Users

### Method 1: PyPI (Recommended)
```bash
pip install gemcli
gem start
```

### Method 2: GitHub Direct
```bash
pip install git+https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
gem start
```

### Method 3: Local Development
```bash
git clone https://github.com/Aniketh78/Gemini-Terminal-Tool-GEM-CLI.git
cd GemCLI
pip install -e .
gem start
```

---

## 🔄 Updating Your Package

When you release a new version:

### 1. Update Version Number

Edit `pyproject.toml`:
```toml
version = "1.0.1"  # or "1.1.0" for features, "2.0.0" for breaking changes
```

### 2. Clean Old Builds

```bash
# Windows
rmdir /s /q dist build
rmdir /s /q gemcli_tool.egg-info gem_cli.egg-info

# Mac/Linux
rm -rf dist build *.egg-info
```

### 3. Rebuild and Upload

```bash
python -m build
python -m twine upload dist/*
```

---

## 📝 Pre-Publishing Checklist

- [x] Package name is unique on PyPI (checked: `gemcli-tool`)
- [x] `pyproject.toml` has correct metadata
- [x] `README.md` is comprehensive
- [x] `LICENSE` file exists (MIT)
- [x] GitHub repository is public
- [x] Entry point `gem start` is configured
- [ ] Test installation locally: `pip install -e .`
- [ ] Test the command: `gem start`
- [ ] Create a GitHub release with tag `v1.0.0`
- [ ] Write CHANGELOG.md

---

## 🐛 Troubleshooting

### "Package already exists"
If the package name is taken, update in `pyproject.toml`:
```toml
name = "gemcli-89p13"  # Add your username
```

### "Invalid distribution files"
Clean and rebuild:
```bash
rm -rf dist build *.egg-info
python -m build
```

### "Authentication failed"
- Make sure you're using `__token__` as username
- Check your API token is valid and not expired
- Use `.pypirc` file for easier authentication
3. **Pre-release**: Upload to Test PyPI
4. **Production**: Upload to PyPI + GitHub Release

## 🎯 Marketing Your CLI

After publishing:

1. **Update README.md** with:
   - Badges (version, downloads, license)
   - Screenshots/GIFs
   - Clear installation instructions
   - Quick start guide

2. **Create a Demo GIF**:
   ```bash
   # Use tools like:
   # - asciinema (terminal recorder)
   # - TerminalGIF
   # - Windows Terminal + ScreenToGif
   ```

3. **Social Media**:
   - Post on Reddit: r/Python, r/programming
   - Tweet with #Python #CLI #AI
   - Share on Dev.to
   - LinkedIn post

4. **Documentation Site** (optional):
   - Use GitHub Pages
   - Add API docs
   - Tutorial videos

## 🔐 Security Notes

- Never commit `.gemini_cookies.json` (already in .gitignore)
- Use PyPI API tokens instead of password
- Enable 2FA on PyPI account
- Review all code before publishing

## 📊 Monitoring

After release:

- **PyPI Stats**: https://pypistats.org/packages/gem-cli
- **GitHub Insights**: Star count, forks, issues
- **Download Count**: Track adoption

## 🆘 Troubleshooting

### "gem command not found" after install

**Windows**: Add Python Scripts folder to PATH
```powershell
# Usually: C:\Users\USERNAME\AppData\Local\Programs\Python\Python3X\Scripts
```

**Mac/Linux**: Add ~/.local/bin to PATH
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Package name already taken on PyPI

Change the name in `pyproject.toml`:
```toml
name = "gemcli-ai"  # or "gemini-terminal-cli"
```

---

## 🎉 Quick Start Commands for You

```bash
# 1. Build the package
python -m build

# 2. Test locally
pip install -e .
gem  # Test it works

# 3. Push to GitHub
git add .
git commit -m "chore: prepare for release"
git push origin main

# 4. Create GitHub release with wheel file

# 5. Upload to PyPI (when ready)
python -m twine upload dist/*
```

Now anyone in the world can install your CLI with:
```bash
pip install gem-cli
gem
```

🚀 **You're ready to share GEM CLI with the world!**
