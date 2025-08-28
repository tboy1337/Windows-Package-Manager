# Windows Package Manager GUI

A modern, user-friendly GUI application for managing Windows packages using the Windows Package Manager (winget).

## Features

- **Intuitive GUI**: Easy-to-use graphical interface built with Python Tkinter
- **Package Search**: Search for packages using winget with real-time results
- **Batch Installation**: Select and install multiple packages at once
- **Profile Management**: Save and load package selection profiles
- **Category Organization**: Browse packages organized by categories
- **Export Scripts**: Generate batch scripts for automated installations
- **Comprehensive Logging**: Detailed logging for troubleshooting and auditing
- **Configuration Management**: Customizable settings and preferences
- **100% Test Coverage**: Thoroughly tested with comprehensive test suite
- **Production Ready**: Error handling, logging, and robust architecture

## Requirements

- Windows 10 or later
- Windows Package Manager (winget) - typically pre-installed on Windows 11, can be installed from Microsoft Store on Windows 10
- Python 3.8 or later
- Administrator privileges (for package installations)

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/tboy1337/Windows-Package-Manager.git
   cd Windows-Package-Manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Launch the application** - Run `main.py` or use the installed entry point
2. **Browse packages** - Use category tabs to explore available software
3. **Search packages** - Type in the search box to find specific software
4. **Select packages** - Check the boxes for packages you want to install
5. **Install packages** - Click "Install Selected" to begin installation
6. **Save profiles** - Save your selections as profiles for future use
7. **Export scripts** - Generate batch scripts for automated deployment

## Configuration

The application creates a `config.json` file with default settings. You can modify:

- Window size and appearance
- Winget timeout settings
- Logging preferences
- UI behavior options

## Logging

Logs are automatically created in the `logs/` directory with:
- Daily log files with timestamps
- Debug level logging to files
- Warning+ level logging to console
- Automatic log rotation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass and maintain 100% coverage
5. Run linting: `pylint core gui main.py`
6. Format code: `black core gui main.py`
7. Submit a pull request

## Code Quality

- **Pylint Score**: 9.90/10
- **Test Coverage**: 100%
- **Code Formatting**: Black
- **Type Hints**: Comprehensive typing
- **Documentation**: Full docstring coverage

## License

MIT License - see LICENSE.txt for details

## Troubleshooting

### Common Issues

1. **"Winget is not available"**
   - Install Windows Package Manager from Microsoft Store
   - Ensure you're on Windows 10 version 1809 or later

2. **"Administrator privileges required"**
   - Right-click and "Run as administrator"
   - Some packages require elevated permissions

3. **Installation fails**
   - Check logs in the `logs/` directory
   - Verify internet connectivity
   - Ensure package ID is correct

### Getting Help

- Check the logs in `logs/` directory for detailed error information
- Review the configuration in `config.json`
- Ensure winget is working: `winget --version` in Command Prompt
- Verify administrator privileges if needed
