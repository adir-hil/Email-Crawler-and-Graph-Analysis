import random
import scrapy
from scrapy.crawler import CrawlerProcess
import time
import re
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
from scrapy.exceptions import CloseSpider
from graph import Graph



class EmailSpider(scrapy.Spider):

    def __init__(self, seed, time_limit=300, max_pages_to_parse=100, scraped_data_filename='scraped_data',
                 rotate=False,exit_flag=True,**kwargs):
        self.seed = seed
        self.rotate= rotate
        self.crawler_output_filename = scraped_data_filename
        self.time_limit = time_limit
        self.max_pages_to_parse = max_pages_to_parse
        self.force_exit = exit_flag
        super().__init__(**kwargs)

    name = 'my_spider'
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    forbidden_keys = ['tel:', 'mailto:', '.jpg', '.pdf', '.png']

    parse_counter = 0
    start_time = time.time()

    def start_requests(self):
        user_agent = random.choice(USERAGENTS)
        use_rotate = (None, user_agent)[self.rotate]
        urls = self.seed
        for url in urls:
            yield scrapy.Request(headers = {"User-Agent":use_rotate}, url=url, callback=self.parse)

    def parse(self, response):
        print(f"requests in queue: {len(self.crawler.engine.slot.scheduler)}")
        print(f'Count of parsed items:{self.parse_counter}')
        if time.time() - self.start_time > self.time_limit or self.parse_counter >= self.max_pages_to_parse:
            print('Bandwidth_exceeded - Spider closing!')
            if self.force_exit:
                raise CloseSpider('bandwidth_exceeded') # reported bug : https://github.com/scrapy/scrapy/issues/5437
            return
        try:
            html = response.body.decode('utf-8')
        except UnicodeDecodeError:
            return
        # Find mailto's
        self.parse_counter += 1
        mailtos = response.xpath("//a[starts-with(@href, 'mailto')]/@href").getall()
        emails = [mail.replace('mailto:', '') for mail in mailtos]
        emails_to_remove = []
        for email in emails:
            try:
                validate_email(email).email
            except EmailNotValidError as e:
                emails_to_remove.append(email)
        emails = [email for email in emails if (email not in emails_to_remove)]
        body_emails = self.email_regex.findall(html)
        for email in body_emails:
            try:
                validate_email(email).email
                emails.append(email)
            except EmailNotValidError as e:
                pass
        parsed_url = urlparse(response.request.url)
        # get_tld('https://' + email.split('@')[-1], fail_silently=True)]
        links = list(response.xpath("//a/@href").getall())
        for index, link in enumerate(links):
            skip = False
            if not link.startswith("http"):
                links[index] = parsed_url.scheme + '://' + parsed_url.netloc + link
            for key in self.forbidden_keys:
                if key in link:
                    skip = True
                    break
            if skip:
                continue
            yield {
                'domain': parsed_url.netloc,
                'url': response.request.url,
                'link': links[index],
                'emails': set(list(emails))
            }
            try:
                yield scrapy.Request(link, callback=self.parse)
            except ValueError:
                try:
                    yield response.follow(link, callback=self.parse)
                except:
                    pass

    def export_results_to_csv(self, graph_results):
        with open('graph_results.csv', 'w') as f:
            for key in graph_results.keys():
                f.write("%s,%s\n" % (key, graph_results[key]))

    def run_crawler(self):
        process = CrawlerProcess(settings={
            'FEED_URI': self.crawler_output_filename + '.csv',
            'FEED_FORMAT': 'csv',
            'LOG_LEVEL': 'INFO',
            'REDIRECT_ENABLED': False,
            'COOKIES_ENABLED': False,
            'RETRY_ENABLED': False,
            'SCHEDULER_PRIORITY_QUEUE': 'scrapy.pqueues.DownloaderAwarePriorityQueue',
            'DEPTH_PRIORITY': 1,
            'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
            'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
            'DEPTH_LIMIT': 3,
            'CONCURRENT_REQUESTS': 100,
            'REACTOR_THREADPOOL_MAXSIZE': 20,
            'DOWNLOAD_DELAY': random.uniform(0.1, 0.5)
        })
        process.crawl(EmailSpider, input='inputargument', time_limit=self.time_limit,
                      max_pages_to_parse=self.max_pages_to_parse, output_file_name=self.crawler_output_filename,
                      force_exit=self.force_exit,rotate=self.rotate,seed=self.seed)
        process.start()
        output_graph = Graph(graph_input_filename=self.crawler_output_filename)
        output_graph.load_graph_from_scv()
        output_graph.set_edges_attributes()
        output_graph.relabel_nodes_to_integers()
        results = output_graph.get_5_main_emails_of_each_domain()
        self.export_results_to_csv(results)


USERAGENTS = [
    'Windows 10/ Edge browser: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
    'Windows 7/ Chrome browser: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
    'Mac OS X10/Safari browser: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
    'Linux PC/Firefox browser: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Chrome OS/Chrome browser: Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
]
