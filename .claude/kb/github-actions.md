# GitHub Actions

## Topics Covered
- GitHub Actions workflow syntax and configuration
- Python/Django CI/CD pipelines 
- Linting and code quality enforcement
- Security scanning integration
- Performance testing and benchmarks
- Troubleshooting common workflow failures

## Main Content

### GitHub Actions Overview
GitHub Actions is GitHub's native CI/CD platform that allows you to automate software development workflows directly within your repository. It uses YAML-based workflow files stored in `.github/workflows/` to define when and how your code should be built, tested, and deployed.

### Key Components

**Workflows**: YAML files that define automated processes
**Jobs**: Groups of steps that run on the same runner
**Steps**: Individual tasks within a job
**Actions**: Reusable units of code that perform specific tasks
**Runners**: Virtual machines that execute your workflows

### Python/Django Best Practices

#### Essential Actions for Python Projects
- `actions/checkout@v4` - Check out repository code
- `actions/setup-python@v4` - Set up Python environment
- `actions/cache@v3` - Cache dependencies for faster builds
- `actions/upload-artifact@v4` - Upload build artifacts (note: v3 is deprecated)

#### Recommended Testing Strategy
```yaml
strategy:
  matrix:
    python-version: [3.11, 3.12]
```

#### Django-Specific Steps
1. **System Check**: `python manage.py check --settings=test_settings`
2. **Migrations**: `python manage.py migrate --settings=test_settings`
3. **Tests with Coverage**: Use `coverage` for comprehensive test reporting

### Linting and Code Quality

#### Modern Approach (2025)
- **Ruff**: Modern, fast linter and formatter (recommended by GitHub)
- **Black**: Code formatting standard
- **isort**: Import statement organization

#### Traditional Approach
- **flake8**: Python linting with configurable rules
- **Black**: Code formatting
- **isort**: Import sorting

#### Flake8 Configuration Best Practices
```yaml
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics  # Critical errors
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics  # Warnings
```

### Security Scanning

#### Essential Security Tools
- **Safety**: Checks for known security vulnerabilities in dependencies
- **Bandit**: Scans Python code for common security issues

#### Configuration Example
```yaml
safety check --json
bandit -r . -x venv/,htmlcov/,logs/ -f json
```

### Performance Testing

#### Basic Performance Monitoring
- Track test suite execution time
- Set reasonable time limits (e.g., 120 seconds for full test suite)
- Use performance benchmarks to catch regressions

### Common Issues and Solutions

#### Deprecated Actions
**Problem**: `actions/upload-artifact@v3` is deprecated
**Solution**: Upgrade to `actions/upload-artifact@v4`

**Problem**: `actions/setup-python@v4` may be outdated
**Solution**: Use `actions/setup-python@v5` for latest features

#### Linting Failures
**Common Issues**:
- E402: Module level import not at top of file
- F401: Module imported but unused
- F403: Unable to detect undefined names from star imports
- W293: Blank line contains whitespace
- C901: Function is too complex (cyclomatic complexity)

**Solutions**:
- Reorganize imports to top of file
- Remove unused imports
- Replace star imports with explicit imports
- Clean up whitespace
- Refactor complex functions

#### Security Scan Failures
**Bandit Issues**:
- B101: Use of assert detected
- B108: Probable insecure usage of temp file/directory
- B301: pickle module usage

**Safety Issues**:
- Vulnerable dependencies in requirements.txt
- Outdated packages with security fixes

#### Test Environment Issues
**Django Test Settings**:
- Use separate test settings file (`test_settings.py`)
- Disable auto-worker spawning: `DISABLE_AUTO_WORKER_SPAWN = True`
- Use in-memory database for faster tests
- Mock external API calls

### Workflow Optimization

#### Caching Strategy
```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

#### Matrix Testing
Run tests across multiple Python versions to ensure compatibility.

#### Artifact Management
- Upload coverage reports for analysis
- Store test logs on failure
- Upload HTML coverage reports for detailed review

## Local Considerations

### Art Factory Project Specifics
The Art Factory project uses a comprehensive 4-job CI pipeline:

1. **Test Job**: Runs Django tests with coverage across Python 3.11 and 3.12
2. **Lint Job**: Uses flake8, black, and isort for code quality
3. **Security Job**: Runs safety and bandit for security scanning
4. **Performance Job**: Monitors test execution time with 120-second limit

### Environment Variables
- Mock API keys in CI: `FAL_KEY`, `REPLICATE_API_TOKEN`
- Use test-specific settings to avoid production interference
- Disable features that cause issues in CI (worker spawning, external calls)

### macOS Development vs Linux CI
- CI runs on `ubuntu-latest` while development is on macOS
- Ensure cross-platform compatibility
- Test locally with similar Python versions as CI

## Metadata
- **Last Updated**: 2025-06-08
- **Version**: GitHub Actions current as of June 2025
- **Sources**: 
  - [GitHub Actions Documentation](https://docs.github.com/en/actions)
  - [Building and Testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
  - Art Factory CI Pipeline (.github/workflows/django.yml)
  - GitHub Issues #51-#54 (CI failure investigation)