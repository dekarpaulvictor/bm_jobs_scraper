# Python Web Scraper For BrighterModay Jobs

This is a command line Python application that uses 
[Selenium](https://www.selenium.dev/) Python bindings
in combination with a headless Chrome browser and the amazing 
[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) library
to scrape [_BrighterMonday_](https://brightermonday.co.ke) job advertisements,
store them in a `json` file and allow the user to search for specific jobs based 
on job title, location, company, date posted and 'I feel lucky' to search by all
the other criteria if they know what they're looking for.

### Installation

It's best if you do this in a virtual environment using Python 3

1. Clone this repository and change into the repository's root folder.

   `git clone https://github.com/dekarpaulvictor/bm_jobs_scraper.git`

2. Create a virtual enviroment

   `python -m venv .`

3. Activate the virtual enviroment

   `source bin/activate`

4. Install needed modules, found in the `requirements.txt` file

   `python -m pip install -r requirements.txt`

5. Download the Chrome web driver. Make sure it matches the installed version of
   Google Chrome on your computer.
  [Chrome web driver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

6. Unzip the driver package and copy the `chromedriver` executable to your
   virtual environment's `bin` folder so it can be located in the environment's
   PATH

7. Switch to the `src` folder and run the app. You can add `--help` to
   see available options

   `python bmscraper.py --help`

