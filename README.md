# Winget Package Manager 🚀

A sleek, user-friendly GUI application built with Python and Tkinter to simplify package management on Windows using Winget. Browse categorized apps, search for packages, select and install multiple apps with ease, save profiles, and more!

## 🌟 Features

- **Categorized App Browsing**: Explore apps organized into categories like Web Browsers, Productivity, Media, and more.
- **Powerful Search**: Quickly find packages using Winget's search capabilities.
- **Multi-Selection & Installation**: Select multiple apps and install them in a multi-threaded manner with automatic retries.
- **Profile Management**: Save and load your app selections for quick setups (stored in SQLite database).
- **Export Scripts**: Generate installation scripts for your selected packages.
- **Installation Logging**: Real-time logs of installation progress.
- **Admin Checks & Silent Installs**: Ensures smooth installations with necessary privileges.
- **Robust Testing**: Comprehensive unit tests with high coverage for reliability.

## 📋 Requirements

- Windows 10 or later (with Winget installed)
- Python 3.6+
- Tkinter (included with Python standard library)
- SQLite (included with Python standard library)

No additional packages required! All dependencies are standard Python libraries.

## 🛠 Installation

1. Clone the repository:
   ```
   git clone https://github.com/tboy1337/winget-manager.git
   cd winget-manager
   ```

2. Run the application:
   ```
   python main.py
   ```

**Note**: For installations to work, run the app as Administrator. Winget must be available on your system.

## 🚀 Usage

- **Browse Categories**: Use the tabs to view apps by category.
- **Search**: Type in the search bar to find specific packages.
- **Select Apps**: Check the boxes next to apps you want to install.
- **Install**: Click "Install Selected" to start the installation process.
- **Profiles**: Save your current selections or load previous ones.
- **Export**: Generate a script for batch installations.

For detailed logs, check the bottom panel during installations.

## 🤝 Contributing

Contributions are welcome! Please fork the repo and submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
