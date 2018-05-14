/*
    This is a web scraper application that can be used to scrape job
    advertisement pages from brightermonday.co.ke, save the results in a json file
    and retrieve results based on search criteria - job title, location, company.
    
    Author: Victor Paul
*/

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
import json
import os
import collections

baseUrl = 'https://www.brightermonday.co.ke/'
searchResultsUrl = baseUrl + 'search/result'
jobBaseUrl = baseUrl + 'jobs/'
# json file name regex
# '^(brightermondayjobs)\_[0-9]{8,8}\-[0-9]{6,6}\.(json)$'
# Matches, e.g. brightermondayjobs_20161114-103302.json

class BrighterMondayJobsScraper:
    """ Scrapes and stores all job listings from brightermonday.co.ke into a file as json objects
        Logic: The data will be ready for consumption by programs written in other languages
        apart from Python
    """

    def __init__(self):
        self.driver = webdriver.PhantomJS()
        self.driver.set_window_size(1024, 768)
        self.uiWindow = """
        ----------------------------------------------------------------------------------------
        Scraper: BrighterMondayJobs
        Version: 0.1
        ----------------------------------------------------------------------------------------
        Main Menu

        [1] Scrape
        [2] Search
        [3] Exit
        """

    def scrape_jobs(self):
        self.driver.get(searchResultsUrl)

        jobs = []
        next_page = 2

        while True:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            job_sections = soup.find_all('article', {'class': 'search-result'})
            current_page = next_page - 1
            print("Scraping page {!s}".format(current_page))
            for job_section in job_sections:
                # We use Python's OrderedDict Collections method to store and retrieve data in the order
                # they are stored, unlike the traditional dictionary
                job = collections.OrderedDict()

                job['Title'] = job_section.find('a', {'class': 'search-result__job-title'}).h3.text.strip()
                job['Link'] = job_section.find('a', {'class': 'search-result__job-title'})['href']
                job['BriefDesc'] = job_section.find('article', {'class': 'search-result__content'}).text.strip()
                job_location = job_section.find('div', {'class': 'search-result__location'})
                job_location = job_location.a.text.strip()
                job['Location'] = job_location
                if job_section.find('div', {'class': 'search-result__job-salary'}):
                    if job_section.find('div', {'class': 'search-result__job-salary'}). \
                            find('span', {'class': 'search-result__currency-symbol'}):
                        currency_symbol = job_section.find('div', {'class': 'search-result__job-salary'})
                        currency_symbol = currency_symbol.find('span', {'class': 'search-result__currency-symbol'})
                        currency_symbol = currency_symbol.text.strip()
                    else:
                        currency_symbol = ''
                    salary_text = job_section.find('div', {'class': 'search-result__job-salary'})
                    salary_text = salary_text.find(text=True, recursive=False).strip()
                    job['Salary'] = currency_symbol + salary_text
                else:
                    job['Salary'] = 'Not provided'
                job['Type'] = job_section.find('div', {'class': 'search-result__job-type'}).text.strip()
                if job_section.find('div', {'class': 'search-result__job-meta'}).a:
                    poster_text = job_section.find('div', {'class': 'search-result__job-meta'})
                    poster_text = poster_text.a.text.strip()
                    job['Poster'] = poster_text
                else:
                    job['Poster'] = 'Anonymous'
                if job_section.find('div', {'class': 'search-result__job-category'}).a:
                    job_category = job_section.find('div', {'class': 'search-result__job-category'})
                    job_category = job_category.a.text.strip()
                    job['Category'] = job_category
                else:
                    job['Category'] = ''

                jobs.append(job)

            try:
                next_page_elem = self.driver.find_element_by_xpath("//a[@rel='next']")
            except NoSuchElementException:
                print('No other pages found. Finishing scraping job.')
                break
            else:
                next_page_link = soup.find('a', text='{!s}'.format(next_page))
                if next_page_link:
                    next_page_elem.click()
                    next_page += 1
                    sleep(0.75)
                else:
                    break

        return jobs

    def scrape(self):
        print('Beginning scraping operation...')
        jobs = self.scrape_jobs()
        total_jobs = len(jobs)
        print('Scraping complete.')
        print('Scraped job listings = {} jobs'.format(total_jobs))

        # Save jobs to file
        file_name = 'brightermondayjobs_{}.json'.format(datetime.now().strftime('%Y%m%d-%H%M%S'))
        print('Saving to file: {}'.format(file_name))
        with open(file_name, 'w') as f:
            json.dump(jobs, f)

        # Print jobs to screen
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

    def search_scraped_jobs(self):

        search_menu = """
        Scraper: BrighterMondayJobs
        Version: 1.0
        ----------------------------------------------------------------------------------------
        Search Menu

        Search scraped jobs by:
        [1] Job Title
        [2] Location
        [3] Company
        [4] All three
        [5] Exit to Main Menu

        """

        # Load data from json file
        # TODO: Let user pick which file to load data from

        jobs = []
        with open('./brightermondayjobs_20161201-183630.json', 'r') as f:
            jobs = json.load(f)

        def search_by_title(title):
            match_found = False
            jobs_ = jobs

            for job in jobs_:
                if title.lower() in job['Title'].lower():
                    match_found = True
                    print('{:20} : {}'.format('Title', job['Title']))
                    print('{:20} : {}'.format('Category', job['Category']))
                    print('{:20} : {}'.format('Location', job['Location']))
                    print('{:20} : {}'.format('Brief Description', job['BriefDesc']))
                    print('{:20} : {}'.format('Posted by', job['Poster']))
                    print('{:20} : {}'.format('Type', job['Type']))
                    print('{:20} : {}'.format('Salary', job['Salary']))
                    print('{:20} : {}'.format('Link', job['Link']))
                    print()

            if not match_found:
                print('No matches found. Sorry.')

        def search_by_location(location):
            match_found = False
            jobs_ = jobs

            for job in jobs_:
                if location.lower() in job['Location'].lower():
                    match_found = True
                    print('{:20} : {}'.format('Title', job['Title']))
                    print('{:20} : {}'.format('Category', job['Category']))
                    print('{:20} : {}'.format('Location', job['Location']))
                    print('{:20} : {}'.format('Brief Description', job['BriefDesc']))
                    print('{:20} : {}'.format('Posted by', job['Poster']))
                    print('{:20} : {}'.format('Type', job['Type']))
                    print('{:20} : {}'.format('Salary', job['Salary']))
                    print('{:20} : {}'.format('Link', job['Link']))
                    print()

            if not match_found:
                print('No matches found. Sorry.')

        def search_by_postedby(poster):
            match_found = False
            jobs_ = jobs

            for job in jobs_:
                if poster.lower() in job['Poster'].lower():
                    match_found = True
                    print('{:20} : {}'.format('Title', job['Title']))
                    print('{:20} : {}'.format('Category', job['Category']))
                    print('{:20} : {}'.format('Location', job['Location']))
                    print('{:20} : {}'.format('Brief Description', job['BriefDesc']))
                    print('{:20} : {}'.format('Posted by', job['Poster']))
                    print('{:20} : {}'.format('Type', job['Type']))
                    print('{:20} : {}'.format('Salary', job['Salary']))
                    print('{:20} : {}'.format('Link', job['Link']))
                    print()

            if not match_found:
                print('No matches found. Sorry.')

        def search_by_all(title, location, poster):
            match_found = False
            jobs_ = jobs

            for job in jobs_:
                if (title.lower() in job['Title'].lower()) and (location.lower() in job['Location'].lower()) \
                        and (poster.lower() in job['Poster'].lower()):
                    match_found = True
                    print('{:20} : {}'.format('Title', job['Title']))
                    print('{:20} : {}'.format('Category', job['Category']))
                    print('{:20} : {}'.format('Location', job['Location']))
                    print('{:20} : {}'.format('Brief Description', job['BriefDesc']))
                    print('{:20} : {}'.format('Posted by', job['Poster']))
                    print('{:20} : {}'.format('Type', job['Type']))
                    print('{:20} : {}'.format('Salary', job['Salary']))
                    print('{:20} : {}'.format('Link', job['Link']))
                    print()

            if not match_found:
                print('No matches found. Sorry.')

        while True:
            os.system('clear')
            print(search_menu)
            print('Total jobs found: {!s}'.format(len(jobs)))
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
                title_name = input('Enter job title: ')
                location_name = input('Enter location: ')
                company_name = input('Enter company name: ')
                print()
                search_by_all(title_name, location_name, company_name)
                break
            elif search_menu_option == '5':
                break
            else:
                print('Wrong option.')
                sleep(2)
                break


if __name__ == '__main__':
    while True:
        os.system('clear')
        scraper = BrighterMondayJobsScraper()
        print(scraper.uiWindow)
        main_menu_option = input('Option: ')
        if main_menu_option == '1':
            scraper.scrape()
            break
        elif main_menu_option == '2':
            scraper.search_scraped_jobs()
            break
        elif main_menu_option == '3':
            print('Exiting.')
            break
        else:
            print('Wrong option.')
            sleep(2)
