import time
import sys
import os
import argparse
import urllib
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import PhotoImage

from selenium.webdriver.common.by import By
from ttkthemes import ThemedTk
import validators
from tkinter import messagebox
from urllib import parse
from pathlib import Path
from bs4 import BeautifulSoup, Comment, Doctype
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from PIL import Image, ImageTk
from tkhtmlview import HTMLLabel
from selenium.webdriver.common.action_chains import ActionChains


class AccessibilityTester:
    def __init__(self, url, required_degree=None, chosen_driver="chrome", headless=False,
                 screenshots=False, browser_height=1080, browser_width=1920, follow=False):
        self.url = url
        self.required_degree = required_degree
        self.chosen_driver = chosen_driver
        self.headless = headless
        self.screenshots = screenshots
        self.browser_height = browser_height
        self.browser_width = browser_width
        self.follow = follow
        self.driver = None
        self.page = None
        self.correct = {"doc_language": 0, "alt_texts": 0, "input_labels": 0, "buttons": 0, "links": 0,
                        "color_contrast": 0}
        self.wrong = {"doc_language": 0, "alt_texts": 0, "input_labels": 0, "empty_buttons": 0, "empty_links": 0,
                      "color_contrast": 0}
        self.visited_links = []
        self.wrong_elements = []
        self.html_page = ''
        self.current_element = ''

    def start_driver(self):
        """This function starts the webdriver with the set configuration of the instance"""
        if self.chosen_driver == "chrome":
            options = ChromeOptions()
            options.headless = self.headless
            options.add_argument("--log-level=3")
            self.driver = webdriver.Chrome(options=options)

        elif self.chosen_driver == "firefox":
            options = FirefoxOptions()
            options.headless = self.headless
            options.add_argument("--log-level=3")
            self.driver = webdriver.Firefox(options=options)

        elif self.chosen_driver == "edge":
            options = EdgeOptions()
            options.use_chromium = True
            options.headless = self.headless
            options.add_argument("--log-level=3")
            self.driver = webdriver.Edge(options=options)

        elif self.chosen_driver == "safari":
            options = SafariOptions()
            options.headless = self.headless
            options.add_argument("--log-level=3")
            self.driver = webdriver.Safari(options=options)
        else:
            raise Exception("Webdriver must be one of: Chrome, Firefox, Edge, Opera, Safari")

        self.driver.set_window_size(self.browser_width, self.browser_height)
        if 'www' == self.url.split('.')[0]:
            self.url = f'https://{self.url[4:]}'
        self.driver.get(self.url)
        print(self.url)
        self.page = BeautifulSoup(self.driver.page_source, "html.parser")

        # make sure that the screenshots directory exists when screenshots are enabled
        if self.screenshots == 'True':
            Path("./screenshots").mkdir(parents=True, exist_ok=True)

    def test_page(self):
        """This function executes the tests for the current page. If tests for subpages are enabled, it will also test all subpages"""
        self.page = BeautifulSoup(self.driver.page_source, "html.parser")
        print("\n\n" + self.driver.current_url + "\n---------------------")
        self.check_doc_language()
        self.check_alt_texts()
        self.check_input_labels()
        self.check_buttons()
        self.check_links()
        self.check_color_contrast()

        if self.screenshots == 'True':
            dir_path = os.path.dirname(os.path.realpath(__file__))
            hostname = urllib.parse.urlparse(self.driver.current_url).hostname
            self.driver.get_screenshot_as_file(dir_path + "/screenshots/" + hostname + "-" + str(time.time()) + ".png")

        if self.follow:
            self.visited_links.append(self.driver.current_url)

            # get all links on the page and iterate over the list of links
            link_list = self.driver.find_elements(by="tag name", value="a")
            for i in range(len(link_list)):
                self.driver.execute_script("elements = document.getElementsByTagName('a'); \
                                            for (var element of elements) {element.setAttribute('target', '')}")
                link = link_list[i]

                # get the full link and check if it needs to be visited
                full_link = str(urllib.parse.urljoin(self.url, link.get_attribute("href")))
                if not link.is_displayed() or link.get_attribute("href") == "" or link.get_attribute("href") is None \
                        or full_link == self.driver.current_url or full_link in self.visited_links:
                    continue
                link_url = link.get_attribute("href")

                # open the link in a new browser window
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[len(self.driver.window_handles) - 1])
                self.driver.get(link_url)

                # get back to the previous window when the link should not be tested
                if self.driver.current_url in self.visited_links or not urllib.parse.urlparse(
                        self.url).hostname in self.driver.current_url:
                    self.driver.switch_to.window(self.driver.window_handles[self.driver.window_handles.index(
                        self.driver.current_window_handle) - 1])
                    continue

                self.test_page()

            # self.driver.switch_to.window(
            #     self.driver.window_handles[self.driver.window_handles.index(self.driver.current_window_handle) - 1])

    def check_doc_language(self):
        """This function checks if the doc language is set (3.1.1 H57)"""
        # check if language attribute exists and is not empty
        lang_attr = self.page.find("html").get_attribute_list("lang")[0]
        if not lang_attr is None and not lang_attr == "":
            # print("  Document language is set")
            self.correct["doc_language"] += 1
        elif not lang_attr is None:
            # print("x Document language is empty")
            self.wrong["doc_language"] += 1
        else:
            # print("x Document language is missing")
            self.wrong["doc_language"] += 1

    def check_alt_texts(self):
        """This function checks if all images on the page have an alternative text (1.1.1 H37)"""
        # get all img elements
        img_elements = self.page.find_all("img")
        for img_element in img_elements:
            # check if img element has an alternative text that is not empty
            alt_text = img_element.get_attribute_list('alt')[0]
            if alt_text and alt_text != "":
                # print("  Alt text is correct", xpath_soup(img_element))
                self.correct["alt_texts"] += 1
            elif alt_text:
                # print("x Alt text is empty", xpath_soup(img_element))
                self.wrong["alt_texts"] += 1
                self.wrong_elements.append(img_element)
                self.highlight_element(img_element, 'empty alt text')
                self.html_page += str(img_element) + '\n'
            else:
                # print("x Alt text is missing", xpath_soup(img_element))
                self.wrong["alt_texts"] += 1
                self.wrong_elements.append(img_element)
                self.highlight_element(img_element, 'no alt text')
                self.html_page += str(img_element) + '\n'

    def check_input_labels(self):
        """This function checks if all input elements on the page have some form of label (1.3.1 H44 & ARIA16)"""
        # get all input and label elements
        input_elements = self.page.find_all("input")
        label_elements = self.page.find_all("label")
        for input_element in input_elements:
            # exclude input element of type hidden, submit, reset and button
            if ("type" in input_element.attrs and not input_element['type'] == "hidden" and not input_element[
                                                                                                    'type'] == "submit"
                and not input_element['type'] == "reset" and not input_element[
                                                                     'type'] == "button") or "type" not in input_element.attrs:
                # check if input is of type image and has a alt text that is not empty
                if "type" in input_element.attrs and input_element['type'] == "image" and "alt" in input_element.attrs \
                        and not input_element['alt'] == "":
                    # print("  Input of type image labelled with alt text", xpath_soup(input_element))
                    self.correct["input_labels"] += 1
                # check if input element uses aria-label
                elif "aria-label" in input_element.attrs and not input_element['aria-label'] == "":
                    # print("  Input labelled with aria-label attribute", xpath_soup(input_element))
                    self.correct["input_labels"] += 1
                # check if input element uses aria-labelledby
                elif "aria-labelledby" in input_element.attrs and not input_element['aria-labelledby'] == "":
                    label_element = self.page.find(id=input_element['aria-labelledby'])
                    if not label_element is None:
                        texts_in_label_element = label_element.findAll(string=True)
                        if not texts_in_label_element == []:
                            # print("  Input labelled with aria-labelledby attribute", xpath_soup(input_element))
                            self.correct["input_labels"] += 1
                        else:
                            # print("x Input labelled with aria-labelledby attribute, but related label has no text",
                            #       xpath_soup(input_element))
                            self.wrong["input_labels"] += 1
                            self.wrong_elements.append(input_element)
                            self.highlight_element(label_element, 'empty label')
                            self.html_page += str(input_element) + '\n'
                    else:
                        # print("x Input labelled with aria-labelledby attribute, but related label does not exist",
                        #       xpath_soup(input_element))
                        self.wrong["input_labels"] += 1
                        self.wrong_elements.append(input_element)
                        self.highlight_element(input_element, 'no label')
                        self.html_page += str(input_element) + '\n'
                else:
                    # check if input element has a corresponding label element
                    label_correct = False
                    for label_element in label_elements:
                        # check if "for" attribute of label element is identical to "id" of input element
                        if "for" in label_element.attrs and "id" in input_element.attrs and label_element['for'] == \
                                input_element['id']:
                            label_correct = True
                    if label_correct:
                        # print("  Input labelled with label element", xpath_soup(input_element))
                        self.correct["input_labels"] += 1
                    else:
                        # print("x Input not labelled at all", xpath_soup(input_element))
                        self.wrong["input_labels"] += 1
                        self.wrong_elements.append(input_element)
                        self.highlight_element(input_element, 'empty button')
                        self.html_page += str(input_element) + '\n'

    def check_buttons(self):
        """This function checks if all buttons and input elements of the types submit, button and reset have some
        form of content (1.1.1 & 2.4.4)"""
        # get all buttons and input elements of the types submit, button and reset
        input_elements = self.page.find_all("input", type=["submit", "button", "reset"])
        button_elements = self.page.find_all("button")

        for input_element in input_elements:
            # check if input element has a value attribute that is not empty
            if "value" in input_element.attrs and not input_element['value'] == "":
                # print("  Button has content", xpath_soup(input_element))
                self.correct["buttons"] += 1
            else:
                # print("x Button is empty", xpath_soup(input_element))
                self.wrong["empty_buttons"] += 1
                self.wrong_elements.append(input_element)
                self.highlight_element(input_element, 'empty button')
                self.html_page += str(input_element) + '\n'

        for button_element in button_elements:
            # check if the button has content or a title
            texts = button_element.findAll(string=True)
            if not texts == [] or ("title" in button_element.attrs and not button_element["title"] == ""):
                # print("  Button has content", xpath_soup(button_element))
                self.correct["buttons"] += 1
            else:
                # print("x Button is empty", xpath_soup(button_element))
                self.wrong["empty_buttons"] += 1
                self.wrong_elements.append(button_element)
                self.highlight_element(button_element, 'empty button')
                self.html_page += str(button_element) + '\n'

    def check_links(self):
        """This function checks if all links on the page have some form of content (2.4.4 G91 & H30)"""
        # get all a elements
        link_elements = self.page.find_all("a")
        for link_element in link_elements:
            # check if link has content
            texts_in_link_element = link_element.findAll(string=True)
            img_elements = link_element.findChildren("img", recursive=False)
            all_alt_texts_set = True
            for img_element in img_elements:
                alt_text = img_element.get_attribute_list('alt')[0]
                if alt_text is None or alt_text == "":
                    all_alt_texts_set = False
            if not texts_in_link_element == [] or (not img_elements == [] and all_alt_texts_set):
                # print("  Link has content", xpath_soup(link_element))
                self.correct["links"] += 1
            else:
                # print("x Link is empty", xpath_soup(link_element))
                self.wrong["empty_links"] += 1
                self.wrong_elements.append(link_element)
                self.highlight_element(link_element, 'empty link')
                self.html_page += str(link_element) + '\n'

    def check_color_contrast(self):
        """This function checks if all texts on the page have high enough contrast to the color of the background (1.4.3 G18 & G145 (& 148))"""
        # exclude script, style, title and empty elements as well as doctype and comments
        texts_on_page = extract_texts(self.page)
        input_elements = self.page.find_all("input")
        elements_with_text = texts_on_page + input_elements
        for text in elements_with_text:
            selenium_element = self.driver.find_element(by="xpath", value=xpath_soup(text))
            # exclude invisible texts
            element_visible = selenium_element.value_of_css_property('display')
            if not element_visible == "none" and \
                    (not text.name == "input" or (
                            text.name == "input" and "type" in text.attrs and not text['type'] == "hidden")):
                text_color = convert_to_rgba_value(selenium_element.value_of_css_property('color'))
                background_color = get_background_color(self.driver, text)

                # calculate contrast between text color and background color
                contrast = get_contrast_ratio(eval(text_color[4:]), eval(background_color[4:]))

                # get font size and font weight
                font_size = selenium_element.value_of_css_property('font-size')
                font_weight = selenium_element.value_of_css_property('font-weight')

                if not font_size is None and font_size.__contains__("px") and \
                        (int(''.join(filter(str.isdigit, font_size))) >= 18 or (
                                (font_weight == "bold" or font_weight == "700"
                                 or font_weight == "800" or font_weight == "900" or text.name == "strong")
                                and int(''.join(filter(str.isdigit, font_size))) >= 14)):
                    if contrast >= 3:
                        # print("  Contrast meets minimum requirements", xpath_soup(text), text_color, background_color)
                        self.correct["color_contrast"] += 1
                    else:
                        # print("x Contrast does not meet minimum requirements", xpath_soup(text), text_color,
                        #       background_color)
                        self.wrong["color_contrast"] += 1
                        self.wrong_elements.append(text)
                        self.highlight_element(text, 'bad contrast')
                        self.html_page += str(text) + '\n'
                else:
                    if contrast >= 4.5:
                        # print("  Contrast meets minimum requirements", xpath_soup(text), text_color, background_color)
                        self.correct["color_contrast"] += 1
                    else:
                        # print("x Contrast does not meet minimum requirements", xpath_soup(text), text_color,
                        #       background_color)
                        self.wrong["color_contrast"] += 1
                        self.wrong_elements.append(text)
                        self.highlight_element(text, 'bad contrast')
                        self.html_page += str(text) + '\n'


    def highlight_element(self, element, warning):
        try:
            xpath = self.get_element_xpath(element)
            # Get element in web driver (browser window for test)
            web_elements = self.driver.find_elements(By.XPATH, xpath)

            for element in web_elements:
                # Create colored border around element
                self.driver.execute_script("arguments[0].style.border='0.5rem dashed orange';", element)
                # self.driver.execute_script(f"arguments[0].appendChild(document.createTextNode('{warning}'))", web_element)
                # self.driver.execute_script(f"arguments.textContent='{warning}'", web_element)

        except Exception as e:
            print(e)

    def multiple_row_configure(self, frame, start_index, end_index, weight):
        i = start_index
        while i <= end_index:
            frame.rowconfigure(i, weight=weight)
            i += 1

    def multiple_column_configure(self, frame, start_index, end_index, weight):
        i = start_index
        while i <= end_index:
            frame.columnconfigure(i, weight=weight)
            i += 1

    def exit_gui(self, window):
        window.destroy()

    def show_elements_window(self, event):
        window = ThemedTk(theme='plastik')
        window.title('Wrong Elements')
        windowWidth = 575
        windowHeight = 125
        window.geometry(f'{windowWidth}x{windowHeight}')
        # window.attributes('-topmost',1)
        window.attributes('-topmost', 1)
        frame = tk.Frame(window, relief='groove', borderwidth=3)
        frame.grid(padx=20, pady=20)
        self.html_page = f"""<html>\n\t<body>\n{self.html_page}\n\t</body>\n</html>"""
        # print(self.html_page)
        with open('html_page.html', 'w', encoding='utf-8') as writer:
            writer.write(self.html_page)
        # HTMLLabel(frame,html=self).pack()
        label = ttk.Label(frame, text='Bad elements list')
        label.grid(row=0, column=0)
        self.current_element = tk.StringVar(frame)
        elementsList = ttk.Combobox(frame, values=self.wrong_elements, textvariable=self.current_element, width=60,
                                    height=20)
        elementsList.grid(row=0, column=1, padx=20, pady=20)
        # button = ttk.Button(frame,text='Show')
        # button.grid(row=0,column=2)
        # button.bind('<Button-1>',self.show_element)

    def get_score(self, testScore):
        color = ''
        text = ''
        if self.required_degree == 0:
            if testScore == 100:
                text = 'Webpage is fully accessible, Excellent site'
                # Lime-Green
                color = '#00FF00'
            elif 90 <= testScore < 100:
                text = 'Webpage is almost fully accessible'
                # Lime-Green
                color = '#80FF00'
            elif 80 <= testScore < 90:
                text = 'Webpage has some accessibility problems'
                # Green-Yellow
                color = '#FFFF00'
            elif 70 <= testScore < 80:
                text = 'Webpage has a lot of accessibility problems, this site is not accessible'
                # Red
                color = '#FF8000'
            elif 60 <= testScore < 70:
                text = 'Webpage has too many accessibility problems, this site is not accessible'
                # Red
                color = '#FF0000'
            scoreText = f'Test Score: {testScore}/100'
        else:
            score = self.required_degree - testScore
            if testScore >= self.required_degree:
                text = 'Webpage passed required test score'
                # Lime-Green
                color = '#00FF00'
            elif score <= 10:
                text = f'Webpage failed required test score by {score} points'
                # Red
                color = '#80FF00'
            elif 10 < score <= 20:
                text = f'Webpage failed required test score by {score} points'
                # Red
                color = '#FFFF00'
            elif 20 < score <= 30:
                text = f'Webpage failed required test score by {score} points'
                # Red
                color = '#FF8000'
            elif 30 < score <= 40:
                text = f'Webpage failed required test score by {score} points'
                # Red
                color = '#FF0000'
            scoreText = f'Test Score: {testScore}/100\nRequired Score:{self.required_degree}'
        return scoreText, color, text

    def gui_calculate_results(self):
        correct = sum(self.correct.values())
        false = sum(self.wrong.values())
        # resWindow = tk.Tk()
        resWindow = ThemedTk(theme='plastik')
        resWindow.title('Results')
        resWindow.attributes('-topmost', 1)
        # Configure result window rows and columns to be responsive to window size
        self.multiple_row_configure(resWindow, 0, 1, 1)
        self.multiple_column_configure(resWindow, 0, 0, 1)

        # Create main frame in window, contains all other frames
        mainFrame = ttk.Frame(resWindow)
        mainFrame.grid(row=0, column=0, sticky='nsew')
        # Configure main frame's rows and columns to be responsive to window size
        self.multiple_row_configure(mainFrame, 0, 2, 1)
        self.multiple_column_configure(mainFrame, 0, 1, 1)

        # Attach information frame to main frame
        infoFrame = ttk.Frame(mainFrame, relief='groove', borderwidth=3)
        # Give frame position in main frame's grid
        infoFrame.grid(row=0, column=0, columnspan=2, sticky='nswe')
        # Configure information frame to be responsive to main frame's size
        self.multiple_row_configure(infoFrame, 0, 4, 1)
        self.multiple_column_configure(infoFrame, 0, 0, 1)

        # Attach correct elements frame to main frame
        correctFrame = ttk.Frame(mainFrame, relief='groove', borderwidth=3)
        correctFrame.grid(row=1, column=0, columnspan=2, sticky='nswe')
        # Configure correct elements frame to be responsive to main frame's size
        self.multiple_row_configure(correctFrame, 0, len(self.correct) - 1, 1)
        self.multiple_column_configure(correctFrame, 0, 1, 1)

        # Attach wrong elements frame to main frame
        wrongFrame = ttk.Frame(mainFrame, relief='groove', borderwidth=3)
        wrongFrame.grid(row=2, column=0, columnspan=2, sticky='nswe')
        # Configure wrong elements frame to be responsive to main frame's size
        self.multiple_row_configure(wrongFrame, 0, len(self.wrong) - 1, 1)
        self.multiple_column_configure(wrongFrame, 0, 1, 1)

        ttk.Label(infoFrame, text=f'Webpage URL: {self.url}').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(infoFrame, text=f'Chosen Browser: {self.chosen_driver}').grid(row=1, column=0, padx=5, pady=5,
                                                                                sticky='w')
        ttk.Label(infoFrame, text=f'Required Score: {self.required_degree}').grid(row=2, column=0, padx=5, pady=5,
                                                                                  sticky='w')
        if correct == 0 and false == 0:
            ttk.Label(resWindow, text='Found Nothing').pack()
            init_gui()
        testScore = int(round(correct / (correct + false), 2) * 100)
        scoreText, color, text = self.get_score(testScore)

        ttk.Label(infoFrame, text=scoreText, font=('Arial', 20)).grid(row=3, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(infoFrame, text=text, font=('Arial', 10)).grid(row=4, column=0, padx=5, pady=5, sticky='w')

        ttk.Label(correctFrame, text='Correct:', font=('Arial', 20)).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        i = 1
        for category, value in self.correct.items():
            ttk.Label(correctFrame, text=f"{category.replace('_',' ').title()}:", font=('Arial', 10)).grid(row=i, column=0, padx=10, pady=5,
                                                                                  sticky='w')
            ttk.Label(correctFrame, text=str(value).replace('_', ' ').title(), font=('Arial', 10)).grid(row=i, column=1, padx=10,
                                                                                               sticky='w')
            i += 1

        i = 0
        ttk.Label(wrongFrame, text='Wrong:', font=('Arial', 20)).grid(row=i, column=0, padx=10, pady=5, sticky='w')
        i += 1
        for category, value in self.wrong.items():
            ttk.Label(wrongFrame, text=f"{category.replace('_',' ').title()}:", font=('Arial', 10)).grid(row=i, column=0, padx=10, pady=5,
                                                                                sticky='w')
            ttk.Label(wrongFrame, text=str(value).replace('_', ' ').title(), font=('Arial', 10)).grid(row=i, column=1, padx=10,
                                                                                             sticky='w')
            i += 1
        resultFrame = ttk.Frame(resWindow, relief='groove', borderwidth=3)
        seeElementsButton = ttk.Button(resWindow, text='Show Elements', width=20, padding=(2, 5))
        seeElementsButton.grid(row=1, column=0, pady=5)
        seeElementsButton.bind('<Button-1>', self.show_elements_window)
        windowWidth = int(infoFrame.winfo_screenwidth() * 0.30)
        windowHeight = int(infoFrame.winfo_screenheight() * 0.75)
        resWindow.geometry(f'{windowWidth}x{windowHeight}')
        resWindow.focus()


    def get_element_xpath(self, element):
        try:
            xpath = "//" + element.name
            if element.name == 'img':
                if element.attrs['src']:
                    xpath += f"[@src='{element.attrs['src']}']"
                elif element.attrs['alt']:
                    xpath += f"[@alt='{element.attrs['alt']}]"
            elif element.name == 'a':
                xpath += f"[@href='{element.attrs['href']}']"
            return xpath
        except KeyError as e:
            print(e)

class GuiMainWindow:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

    def init_window(self):
        self.mainWindow.title('Web App Accessibility Tester')
        self.mainWindow.geometry('600x400')  # Set initial window size

        # Create a frame for the content
        frame = ttk.Frame(self.mainWindow, padding=10)
        frame.grid(row=0, column=0, sticky='nsew')
        frame.columnconfigure(0, weight=1)  # Make the frame expand with the window width
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.rowconfigure(10, weight=1)

        # Add style from ttkthemes
        style = ttk.Style()
        style.theme_use('plastik')  # Choose your desired theme

        # Create and configure the labels and input widgets
        ttk.Label(frame, text='Webpage URL:').grid(row=1, column=1, sticky='w', padx=10, pady=5)
        urlEntry = ttk.Entry(frame, width=50)
        urlEntry.grid(row=2, column=1, columnspan=2, sticky='w', padx=10)

        ttk.Label(frame, text='Choose test start time in x seconds. To set the webpage for test:').grid(row=3, column=1,
                                                                                                        columnspan=3,
                                                                                                        sticky='w',
                                                                                                        padx=10, pady=5)
        startTimeScale = tk.Scale(frame, from_=0, to=60, orient='horizontal')
        startTimeScale.grid(row=4, column=1, columnspan=3, sticky='w', padx=10)

        ttk.Label(frame, text='Required Test Grade:').grid(row=5, column=1, columnspan=3, sticky='w', padx=10, pady=5)
        requiredGradeScale = tk.Scale(frame, from_=0, to=100, orient='horizontal')
        requiredGradeScale.grid(row=6, column=1, columnspan=3, sticky='w', padx=10)

        ttk.Label(frame, text='Choose Browser (Default Browser - Chrome):').grid(row=7, column=1, columnspan=3,
                                                                                 sticky='w', padx=10, pady=5)
        driversListBox = ttk.Combobox(frame, values=['Chrome', 'Firefox', 'Edge', 'Safari'])
        driversListBox.set('Chrome')
        driversListBox.grid(row=8, column=1, columnspan=3, sticky='w', padx=10)

        startButton = ttk.Button(frame, text='Start Test', width=10,
                                 command=lambda: self.init_accessibility_test(urlEntry, startTimeScale,
                                                                              requiredGradeScale, driversListBox))
        startButton.grid(row=9, column=2, columnspan=3, sticky='sw', pady=20)

    def init_accessibility_test(self, urlEntry, startTimeScale, requiredGradeScale, driversListBox):
        if len(urlEntry.get()) == 0:
            messagebox.showerror('Error', 'Missing Fields')
        else:
            accessibilityTester = AccessibilityTester(urlEntry.get(), requiredGradeScale.get(),
                                                      driversListBox.get().lower())
            accessibilityTester.start_driver()
            time.sleep(startTimeScale.get())
            accessibilityTester.test_page()
            accessibilityTester.gui_calculate_results()


def init_gui():
    mainWindow = ThemedTk(theme='plastik')
    mainWindow.title('Web App Accessibility Tester')
    icon = PhotoImage(file="/home/daniel/PycharmProjects/AccessibilityTester/accessibility-icon.png")
    mainWindow.iconphoto(True, icon)
    frame = tk.Frame(mainWindow, relief='groove', borderwidth=3)
    urlLabel = ttk.Label(frame, text='Webpage URL:')
    urlEntry = ttk.Entry(frame, width=50)
    startTimeLabel = ttk.Label(frame, text='Choose test start time in x seconds.\nTo set the webpage for test')
    startTimeScale = tk.Scale(frame, from_=0, to=60, orient='horizontal')
    startTimeScale.set(0)
    requiredGradeLabel = ttk.Label(frame, text='Required Test Grade:')
    requiredGradeScale = tk.Scale(frame, from_=0, to=100, orient='horizontal')
    requiredGradeScale.set(0)
    driversLabel = ttk.Label(frame, text='Choose Browser\n(Default Browser - Chrome):')
    listBoxAnswer = tk.StringVar()
    driversListBox = ttk.Combobox(frame, values=['Chrome', 'Firefox', 'Edge', 'Safari'], textvariable=listBoxAnswer)
    driversListBox.set('Chrome')
    startButton = ttk.Button(frame, text='Start Test', width=10)
    frame.grid(padx=10, pady=10)
    guiMainWindow = GuiMainWindow(mainWindow)
    guiMainWindow.init_window()
    # Make frame responsive to all window sizes
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    width = int(mainWindow.winfo_screenwidth() * 0.42)
    height = int(mainWindow.winfo_screenheight() * 0.44)
    mainWindow.geometry(f'{width}x{height}')

    startButton.bind('<Button-1>', guiMainWindow.init_accessibility_test)
    guiMainWindow.mainWindow.mainloop()


def xpath_soup(element):
    # pylint: disable=consider-using-f-string
    """This function calculates the xpath of an element"""
    if element is None:
        return '/html'
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """type: bs4.element.Tag"""
        siblings = parent.find_all(child.name, recursive=False)
        components.append(child.name if 1 == len(siblings)
                          else '%s[%d]' % (child.name, next(i for i, s in enumerate(siblings, 1) if s is child)))
        child = parent
    components.reverse()
    if not components:
        return '/html'
    return '/%s' % '/'.join(components)


def extract_texts(soup):
    """This function extracts all texts from a page"""
    soup2 = soup

    # remove script, style and title elements
    for invisible_element in soup2(["script", "style", "title", "noscript"]):
        invisible_element.extract()

    # remove comments
    comments = soup2.findAll(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()

    # remove doctype
    doctype = soup2.find(string=lambda text: isinstance(text, Doctype))
    if not doctype is None:
        doctype.extract()

    # get all elements with text
    texts = []
    texts_on_page = soup2.findAll(string=True)
    for text in texts_on_page:
        if not text.strip() == "" and not text == "\n":
            texts.append(text.parent)

    return texts


def get_background_color(driver, text):
    """This function returns the background color of a given text"""
    if text is None:
        return "rgba(255,255,255,1)"

    selenium_element = driver.find_element(by="xpath", value=xpath_soup(text))
    background_color = convert_to_rgba_value(selenium_element.value_of_css_property('background-color'))

    if eval(background_color[4:])[3] == 0:
        return get_background_color(driver, text.parent)

    return background_color


def convert_to_rgba_value(color):
    """This function converts a color value to the rgba format"""
    if color[:4] != "rgba":
        rgba_tuple = eval(color[3:]) + (1,)
        color = "rgba" + str(rgba_tuple)

    return color


def get_contrast_ratio(text_color, background_color):
    """This function calculates the contrast ratio between text color and background color"""
    # preparing the RGB values
    r_text = convert_rgb_8bit_value(text_color[0])
    g_text = convert_rgb_8bit_value(text_color[1])
    b_text = convert_rgb_8bit_value(text_color[2])
    r_background = convert_rgb_8bit_value(background_color[0])
    g_background = convert_rgb_8bit_value(background_color[1])
    b_background = convert_rgb_8bit_value(background_color[2])

    # calculating the relative luminance
    luminance_text = 0.2126 * r_text + 0.7152 * g_text + 0.0722 * b_text
    luminance_background = 0.2126 * r_background + 0.7152 * g_background + 0.0722 * b_background

    # check if luminance_text or luminance_background is lighter
    if luminance_text > luminance_background:
        # calculating contrast ration when luminance_text is the relative luminance of the lighter colour
        contrast_ratio = (luminance_text + 0.05) / (luminance_background + 0.05)
    else:
        # calculating contrast ration when luminance_background is the relative luminance of the lighter colour
        contrast_ratio = (luminance_background + 0.05) / (luminance_text + 0.05)

    return contrast_ratio


def convert_rgb_8bit_value(single_rgb_8bit_value):
    """This function converts an rgb value to the needed format"""
    # dividing the 8-bit value through 255
    srgb = single_rgb_8bit_value / 255
    # check if the srgb value is lower than or equal to 0.03928
    if srgb <= 0.03928:
        return srgb / 12.92
    return ((srgb + 0.055) / 1.055) ** 2.4


if __name__ == "__main__":
    root = ThemedTk(theme='plastik')
    icon = PhotoImage(file="/home/daniel/PycharmProjects/AccessibilityTester/accessibility-icon.png")
    root.iconphoto(True, icon)

    guiMainWindow = GuiMainWindow(root)
    guiMainWindow.init_window()

    # Make the window resizable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    root.mainloop()

