from crawler import EmailSpider

seed = ['https://www.example.com/']
crawl_output_filename = 'scraping_data'
crawl = EmailSpider(seed=seed, time_limit=300, scraped_data_filename=crawl_output_filename, max_pages_to_parse=1000,
                    rotate=False, force_exit=True)
crawl.run_crawler()

