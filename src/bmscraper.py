###
#    This is a web scraper application that can be used to scrape job
#    advertisement pages on brightermonday.co.ke, save the results in a json file
#    and retrieve results based on search criteria - job title, location,
#    company, date posted or all four criteria if "you're feeling lucky" ;)
#    
#    Author: Victor Paul 'dekar'
###

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
from collections import OrderedDict
from argparse import ArgumentParser
import urllib.request
import urllib.error
import json
import os
import re
import uuid

BASE_URL = 'https://brightermonday.co.ke/'
JOBS_URL = BASE_URL + 'jobs/it-telecoms'


# json file name regex
# '^(brightermondayjobs)\_[0-9]{8,8}\-[0-9]{6,6}\.(json)$'
# Matches, e.g. brightermondayjobs_20161114-103302.json

class BrighterMondayJobsScraper:
    """ Scrapes and stores all job listings from brightermonday.co.ke into a file as json objects
        Logic: The data will be ready for consumption by programs written in other languages
        apart from Python
    """

    def __init__(self, pages = 5):
        self.pages = pages

    # Will be toggled accordingly in case of errors while scraping for data
    scraping_error = False

    # Init selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_argument('--headless')

    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
    driver.set_window_size(1366, 768)
    driver.implicitly_wait(5)

    # The app's awesome main menu
    uiWindow = """
    ----------------------------------------------------------------------------------------
    Brighter Monday Jobs Scraper
    Version: 1.0
    ----------------------------------------------------------------------------------------
    Main Menu

    [1] Scrape
    [2] Search
    [3] Exit
    """

    # The main scraping function
    def scrape_jobs(self):
        self.driver.get(JOBS_URL)

        # wait for page to load, check for the cookie consent section
        # and programmatically click the agree button

        if self.driver.find_element(By.ID, 'onetrust-accept-btn-handler'):
            print('>>> Found cookie agree button')
            cookie_agree_button = self.driver.find_element(By.ID, 'onetrust-accept-btn-handler')
            cookie_agree_button.click()
            print('>>> Cookie agree button clicked. Waiting for 5 seconds to begin scraping...')
            sleep(5);

        # Array to store scraped jobs as Collections.OrderedDict
        jobs = []

        # Helps keep track of the next page value
        next_page = 2

        while True:
            try:
                current_page = next_page - 1

                # Stop scraping after given number of pages, default = 5
                if current_page == self.pages + 1:
                    break

                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                job_sections = soup.find_all(attrs={"data-cy": "listing-cards-components"})

                for job_section in job_sections:

                    # Skip featured jobs
                    try:
                        if job_section.find('div', class_='flex flex-shrink-0 justify-center items-center w-5 text-xs font-medium text-white uppercase rounded-l-md rounded-bl-none bg-brand-secondary').span.text.strip() == 'FEATURED':
                            print('>>> Skipping featured job')
                            continue
                    except AttributeError:
                        pass

                    # We use Python's OrderedDict data structure to store and retrieve data in the order
                    # they are stored, unlike the in traditional dictionary
                    job = OrderedDict()

                    # Generate UUID for the job
                    job['ID'] = str(uuid.uuid4())

                    if job_section.find('a', class_="relative mb-3 text-lg font-medium break-words focus:outline-none metrics-apply-now text-link-500 text-loading-animate"):
                        job['Title'] = job_section.find('a', class_="relative mb-3 text-lg font-medium break-words focus:outline-none metrics-apply-now text-link-500 text-loading-animate").p.text.strip()
                        job['Link'] = job_section.find('a', class_="relative mb-3 text-lg font-medium break-words focus:outline-none metrics-apply-now text-link-500 text-loading-animate")['href']
                        # use selenium to launch another window to fetch content from the job link
                        # and extract job summary and job description
                        # then close the window
                        try:
                            self.driver.execute_script("window.open('');")
                            self.driver.switch_to.window(self.driver.window_handles[1])
                            self.driver.get(job['Link'])
                            job_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                            job_summary_desc = job_soup.find('article', class_='job__details')
                            # find job summary and job description in the job details section
                            # and store them in the job dict
                            # if not found, store 'No summary available' and 'No description available'
                            # respectively
                            job_summary_desc_list = job_summary_desc.find_all('div', class_='py-5 px-4 border-b border-gray-300 md:p-5')
                            if job_summary_desc_list[0].h3.text.strip() == 'Job Summary':
                                job['Summary'] = str(job_summary_desc_list[0])
                            else:
                                job['Summary'] = 'No summary available'
                            if "Job Description" in job_summary_desc_list[1].h3.text.strip():
                                job['Description'] = str(job_summary_desc_list[1])
                            else:
                                job['Description'] = 'No description available'
                            # job['Description'] = job_summary_desc.text.strip()
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                        except Exception as e:
                            print('>>> Error fetching job summary and description')
                            print(e)
                            job['Summary'] = 'No summary available'
                            job['Description'] = 'No description available'
                    else:
                        job['Title'] = 'No title provided'
                        job['Link'] = 'No link available'

                    if job_section.find('p', class_='text-sm text-link-500'):
                        job_poster = job_section.find('p', class_='text-sm text-link-500').text.strip()
                        job['Poster'] = job_poster
                    else:
                        job['Poster'] = 'No job poster found'

                    if job_section.find('div', class_='flex flex-wrap mt-3 text-sm text-gray-500 md:py-0'):
                        job_location_type_salary = job_section.find('div', class_='flex flex-wrap mt-3 text-sm text-gray-500 md:py-0')
                        job_location_type_salary = job_location_type_salary.find_all('span')
                        job['Location'] = job_location_type_salary[0].text.strip()
                        job['Type'] = job_location_type_salary[1].text.strip()
                        job['Salary'] = job_location_type_salary[2].text.strip()

                    if job_section.find('p', class_='text-sm text-gray-500 text-loading-animate inline-block'):
                        job_category = job_section.find('p', class_='text-sm text-gray-500 text-loading-animate inline-block').text.strip()
                        job['Category'] = job_category.split(":")[1].strip()
                    else:
                        job['Category'] = 'Category not provided'

                    if job_section.find('div', class_='flex flex-row items-start items-center px-5 py-3 w-full border-t border-gray-300'):
                        date_posted = job_section.find('div',
                                class_='flex flex-row items-start items-center px-5 py-3 w-full border-t border-gray-300').p.text.strip()
                        job['Date_Posted'] = date_posted
                    else:
                        job['Date_Posted'] = 'Date posted not provided'

                    # Add scraped data to `jobs` array
                    jobs.append(job)
                print("Scraped page {!s}".format(current_page))

                # Check if we have a next page
                try:
                    next_page_elem = self.driver.find_element(By.XPATH, value="//nav[@role='navigation']/div/a[@rel='next']")
                    # Navigate to next page if we still have more pages to
                    # scrape
                    if next_page_elem and (current_page < self.pages):
                        # next_page_elem.click()
                        print('>>> Navigating to next page and waiting for page to load...')
                        self.driver.get(JOBS_URL + '?page=' + str(next_page))
                        next_page += 1
                        sleep(5) # wait for 1 second before scraping next page
                    else:
                        break
                except NoSuchElementException:
                    print('No other pages found. Finishing scraping job.')
                    break

            except:
                self.scraping_error = True
                print('<<< An error occured. Jobs saved so far will still be available for you to see >>>')
                break

        return jobs

    def scrape(self):
        print('Beginning scraping operation...')
        print('Scraping {} pages...'.format(self.pages))

        jobs = self.scrape_jobs()
        # Report final status of scraping operation
        if self.scraping_error:
            print('Scraping completed but with some errors.')
        else:
            print('Scraping completed successfully.')

        total_jobs = len(jobs)
        print('Scraped job listings = {} jobs'.format(total_jobs))

        # Save jobs to file
        file_name = 'brightermondayjobs_{}.json'.format(datetime.now().strftime('%Y%m%d-%H%M%S'))
        print('Saving to file: {}'.format(file_name))
        with open(file_name, 'w') as f:
            json.dump(jobs, f)

        # Optional: Print jobs to screen
        print()
        print_jobs_to_screen = input('Print jobs to screen? [Y]es or [N]o: ')
        if print_jobs_to_screen.lower() in ['y', 'yes', 'yeah']:
            jobs_to_print = input('Enter number of jobs to print (Total Jobs = {}): '.format(total_jobs))
            jobs_to_print = int(jobs_to_print)
            # Print out the jobs
            for job in jobs[:jobs_to_print]:
                for k, v in job.items():
                    print('{:10} : {}'.format(k, v))
                print()

            print('-----------------------------------------')
            print('Done.')
            print('-----------------------------------------')
        elif print_jobs_to_screen.lower() in ['n', 'no', 'nope']:
            print('Ok. Bye.')
        else:
            print('Wrong input. Exiting.')

    # Loads and searches given json file for matching job listings
    def search_scraped_jobs(self, file_name):

        # The app's awesome search menu
        search_menu = """
        Brighter Monday Jobs Search 
        Version: 1.0
        ----------------------------------------------------------------------------------------
        Search Menu

        Search scraped jobs by:
        [1] Job Title
        [2] Location
        [3] Company
        [4] Date posted ['1 day ago', '2 weeks ago', '1 hour' and so on]
        [5] I feel lucky [search by all four criteria]
        [6] Exit

        """

        # Regular expression to make sure user-provided string is within
        # expectations.
        # Matches patterns like '1 day ago', '4 weeks ago', '5 minutes'...
        date_posted_regexp = re.compile(r'^\d+\s+(minute|hour|day|week|month)s?\s?(ago)?$',
                re.IGNORECASE)

        def print_jobs(title, category, location, poster, type_, salary, link,
                date_posted):
            # The job posted date is stored as '2h', '1d', '5w', etc
            # So we split the time-count and period indicator using
            # Python's awesome list splitting magic and
            # save the print out the date as '2 hour(s)' '1 day(s)', '5 week(s)', etc
            time_count = re.findall(r'\d+', date_posted.lower(), re.IGNORECASE)[0]
            period_indicator = re.findall(r'[a-z]+', date_posted.lower(), re.IGNORECASE)[0]
            period_indicator_full = ''
            if period_indicator == 'm':
                period_indicator_full = 'minute(s)'
            elif period_indicator == 'h':
               period_indicator_full = 'hour(s)'
            elif period_indicator == 'd':
               period_indicator_full = 'day(s)'
            elif period_indicator == 'w':
                period_indicator_full = 'week(s)'
            elif period_indicator == 'mo':
                period_indicator_full = 'month(s)'
            else:
                period_indicator_full = period_indicator
            date_posted = '{} {} ago'.format(time_count, period_indicator_full)

            print('{:20} : {}'.format('Title', title))
            print('{:20} : {}'.format('Category', category))
            print('{:20} : {}'.format('Location', location))
            print('{:20} : {}'.format('Posted by', poster))
            print('{:20} : {}'.format('Type', type_))
            print('{:20} : {}'.format('Salary', salary))
            print('{:20} : {}'.format('Link', link))
            print('{:20} : {}'.format('Date Posted', date_posted))
            print()


        # Compares user-provided date string and values from the file
        # We have to strip some characters from the user-provided string
        # since the string we're comparing it to is like '1d', '3h', and so on
        # Returns true if they match, false otherwise
        def compare_dates(date_1, date_2):
            date_1 = date_1.lower()
            date_1 = date_1.split(' ');
            time_count = date_1[0]
            period_indicator = ''
            # if the user entered 'month[s]' we have to make sure we've
            # extracted 'mo' from the string
            if date_1[1] in 'months':
                period_indicator = date_1[1][:2]
            else:
                period_indicator = date_1[1][:1]
            new_date_1 = '{}{}'.format(time_count, period_indicator)

            return (new_date_1 == date_2)

        # Load data from json file
        jobs = []
        with open(file_name, 'r') as f:
            jobs = json.load(f)

        def search_by_title(title):
            match_found = False
            jobs_ = jobs
            job_count = 0

            for job in jobs_:
                if title.lower() in job['Title'].lower():
                    match_found = True
                    job_count += 1
                    print_jobs(
                        job['Title'],
                        job['Category'],
                        job['Location'],
                        job['Poster'],
                        job['Type'],
                        job['Salary'],
                        job['Link'],
                        job['Date_Posted'],
                    )
            print('Total jobs found: {}'.format(job_count))
            if not match_found:
                print('No matches found. Sorry.')

        def search_by_location(location):
            match_found = False
            jobs_ = jobs
            job_count = 0

            for job in jobs_:
                if location.lower() in job['Location'].lower():
                    match_found = True
                    job_count += 1
                    print_jobs(
                        job['Title'],
                        job['Category'],
                        job['Location'],
                        job['Poster'],
                        job['Type'],
                        job['Salary'],
                        job['Link'],
                        job['Date_Posted'],
                    )
            print('Total jobs found: {}'.format(job_count))
            if not match_found:
                print('No matches found. Sorry.')

        def search_by_postedby(poster):
            match_found = False
            jobs_ = jobs
            job_count = 0

            for job in jobs_:
                if poster.lower() in job['Poster'].lower():
                    match_found = True
                    job_count += 1
                    print_jobs(
                        job['Title'],
                        job['Category'],
                        job['Location'],
                        job['Poster'],
                        job['Type'],
                        job['Salary'],
                        job['Link'],
                        job['Date_Posted'],
                    )
            
            print('Total jobs found: {}'.format(job_count))
            if not match_found:
                print('No matches found. Sorry.')

        def search_by_date_posted(date_posted):
            match_found = False
            jobs_ = jobs
            job_count = 0

            for job in jobs_:
                if compare_dates(date_posted.lower(), job['Date_Posted'].lower()):
                    match_found = True
                    job_count += 1
                    print_jobs(
                        job['Title'],
                        job['Category'],
                        job['Location'],
                        job['Poster'],
                        job['Type'],
                        job['Salary'],
                        job['Link'],
                        job['Date_Posted'],
                    )
            
            print('Total jobs found: {}'.format(job_count))
            if not match_found:
                print('No matches found. Sorry.')

        def search_by_all(title, location, poster, date_posted):
            match_found = False
            jobs_ = jobs
            job_count = 0

            # TODO: Implement regex for date_posted search
            for job in jobs_:
                if (title.lower() in job['Title'].lower()) and (location.lower() in job['Location'].lower()) \
                        and (poster.lower() in job['Poster'].lower() and
                                compare_dates(date_posted.lower(), job['Date_Posted'].lower())):
                    match_found = True
                    job_count += 1
                    print_jobs(
                        job['Title'],
                        job['Category'],
                        job['Location'],
                        job['Poster'],
                        job['Type'],
                        job['Salary'],
                        job['Link'],
                        job['Date_Posted'],
                    )
            print('Total jobs found: {}'.format(job_count))
            if not match_found:
                print('No matches found. It appears you weren\'t so lucky.')

        while True:
            os.system('clear')
            print(search_menu)
            print('Job listings file: {!s}'.format(file_name))
            print('Total jobs in file: {!s}'.format(len(jobs)))
            print()
            search_menu_option = input('Option: ')
            if search_menu_option == '1':
                title_name = input('Enter job title: ')
                print()
                search_by_title(title_name)
                break
            elif search_menu_option == '2':
                location_name = input('Enter location: ')
                print()
                search_by_location(location_name)
                break
            elif search_menu_option == '3':
                company_name = input('Enter company name: ')
                print()
                search_by_postedby(company_name)
                break
            elif search_menu_option == '4':
                date_posted = input('Enter date posted: ')
                if date_posted_regexp.search(date_posted):
                    print()
                    search_by_date_posted(date_posted)
                else:
                    print('Please enter the date posted as {}'.\
                            format('[1 day ago, 2 weeks ago, 2 hours, and so on]'))
                break
            elif search_menu_option == '5':
                title_name = input('Enter job title: ')
                location_name = input('Enter location: ')
                company_name = input('Enter company name: ')
                date_posted = input('Enter date posted: ')
                if date_posted_regexp.search(date_posted):
                    print()
                    search_by_all(title_name, location_name, company_name, date_posted)
                else:
                    print('Please enter the date posted as {}'.\
                            format('[1 day ago, 2 weeks ago, 2 hours, and so on]'))
                break
            elif search_menu_option == '6':
                break
            else:
                print('Wrong option.')
                sleep(2)
                break

if __name__ == '__main__':

    # Initialize the app's argument parser
    parser = ArgumentParser()
    parser.add_argument('-p', '--pages', help='Specify how many pages to scrape')
    parser.add_argument('-f', '--file', help='Specify json file with job listings')
    args = parser.parse_args()

    while True:
        os.system('clear')
        scraper = BrighterMondayJobsScraper()

        # pass in the number of pages to scrape if provided
        if args.pages:
            pages_to_scrape = args.pages
            scraper = BrighterMondayJobsScraper(int(pages_to_scrape))

        print(scraper.uiWindow)
        main_menu_option = input('Option: ')
        if main_menu_option == '1':
            scraper.scrape()
            break
        elif main_menu_option == '2':
            # set the file to load and search, if provided
            if args.file:
                file_name = args.file
                scraper.search_scraped_jobs(file_name)
            else:
                print("You didn't specify a file to search. Please see the help options")
            break
        elif main_menu_option == '3':
            print('Exiting.')
            break
        else:
            print('Wrong option.')
            sleep(2)
