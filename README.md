# Accessibility Tester
Accessibility Tester is a Python program designed to help website owners and developers test the accessibility of their sites. It checks every accessibility aspect of the site, including color contrast, font sizes, alternative text, and more.

## Requirements
Windows OS
AccessibilityTester.exe

## Installation
The current executable is for Linux systems (sorry, using Ubuntu at the moment). If you want to run the program, just follow these steps below.
### Compiling the Python Program
Before running the program, you'll need to compile it into a standalone executable using PyInstaller.
Follow these steps:
1. Open your terminal.
2. Navigate to the directory where your Python script is located.
3. Run the following command to compile the program: ``pyinstaller --onefile AccessibilityTester.py``
Replace `AccessibilityTester.py` with the name of your Python script.

4. After compilation is complete, you can find the executable in the `dist` directory within your project folder. The executable will have the same name as your script but without the '.py' extension.

### Running the Executable
To run the compiled executable, follow these steps:
1. Open your terminal.
2. Navigate to the directory where the compiled executable is located (usually the `dist` directory) and run it.
3. If you're using Linux run the executable using the following command, if needed: ``./AccessibilityTester``




## Usage
Open the program by double-clicking on the AccessibilityTester.exe file.
Enter the URL of the website you want to test in the input field and click on the "Run Test" button.
Wait for the program to finish testing. This may take a few minutes depending on the size and complexity of the website.
View the results in the program window. The results will be grouped by category (e.g. color contrast, font sizes, etc.) and will include detailed information about any accessibility issues found.
Contributing
Contributions to this project are welcome. If you find a bug or have a suggestion for improvement, please create an issue on the GitHub repository.

## Screenshots
![project-screenshot-1](https://github.com/daniel752/Accessibility-Tester/blob/main/images/screenshot-1.png?raw=true)
![project-screenshot-2](https://github.com/daniel752/Accessibility-Tester/blob/main/images/screenshot-2.png?raw=true)
![project-screenshot-3](https://github.com/daniel752/Accessibility-Tester/blob/main/images/screenshot-3.png?raw=true)

## License
This project is licensed under GNU General Public License (GPL).
