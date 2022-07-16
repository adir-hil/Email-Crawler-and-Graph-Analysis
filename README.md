# Email-Crawler-and-Graph-Analysis
Crawling and scraping emails using a scrapy-based broad crawler, results are analyzed using a Networkx Digraph

[README.pdf](https://github.com/adir-hil/Email-Crawler-and-Graph-Analysis/files/9126587/README.pdf) <- open the link to view the readme in a clear PDF format

The scrapy spider is intentionally implemented and executed via a CrawlerProcess and not the scrapy project and shell. The aim is to allow execution of the code without requiring to create a scrapy project, so the crawler is executed using a single .py file.

# Prerequisites:
-	pip install scrapy (2.6.1)
-	pip install  email_validator  (1.2.1)
-	pip install networkx (2.8.4)
-	pip install numpy
# Execution:
Locate main.py, crawler.py, and graph.py in the project's folder, run main.py 
Config details:</br>
The crawler is implemented via the EmailSpider class, its constructer requires the following arguments:
| Parameter | Type | Mandatory | Description | Default |
| :---: | :---: |:---:| :---: | :---: |
| *seed* | list |Y| Includes a list of URLs (strings) for the crawler to begin crawling from|['https://www.example.com/']|
| *time_limit* | Float | N | The time limit for the crawling process (seconds) | 300 |
| *scraped_data_filename* |str | N | The name of the file to be generated includes scrape data (without file extension). | scraped_data |
| *max_pages_to_parse* | int | N |The maximum amount of pages to be scrapped by the crawler.| 100 |
| *rotate* | Bool | N | Whether to switch between different user agents while crawling (helps avoid being banned by sites but affects performance) | False |
| *force_exit** | Bool | N | Whether to force crawler to exit aggressively when bandwidth is exhausted (display harmless error and exits immediately) or wait until all requests in the queue are cleared (no error is displayed  but very slow)  | True |

*This parameters was added since the spider cannot be stopped immeditaly when it reaches the bandwith limit without displaying an excpetion.
This issue is known and reported on https://github.com/scrapy/scrapy/issues/5437, it sechduled to be fixed the next scrapy version (2.6.2). a fix  is already available (pip install -e git+ssh://git@github.com/scrapy/scrapy.git@2.6#egg=scrapy)   but wasn't implement due to compatiblity issues

# Crawler mechanism (EmailSpider class)
The crawler is based on a scrapy library. It starts from the seeds and crawls using a BFS traversal. The scraping process targets links (via href tags) and emails (via regex) on each crawled page.  An item is yielded for each found link, its structure can be seen as a dictionary:</br>  
*{Domain: 'value'(str), URL: 'value'(str), link: 'value'(str),emails: {set of emails}}.*</br>

All the yielded items are stored in a CSV file (stated in the scraped_data_filename argument).

# Graph generation and analysis(Graph class)
The generated graph utilizes the Networkx library. It receives the CSV from the crawler as input and scans each row (item). Each unique URL or link is a node (a URL can also be a link and vice-versa), each node includes a domain and  a set of emails as attributes (nodes' labels are sequential integers for convenience, the URL value is stored as another attribute but acts as an identifier). An edge is a relationship between each URL and the links found on that URL (URL-> Link), so the graph is directed (Digraph), the direction is important for betweenness and closeness centrality calculation.</br>
**Important note:** links that were scraped but not visited during the crawl were also added to the graph as nodes (with an empty email attribute). The rationale was that if a URL with an email has many links that were not visited, we want to reflect its centrality by creating nodes for each of its links as neighbors.

# The 5 most important emails per domain

Each email was assigned a score which was used to rank email importance in each domain.

![score_formula](https://user-images.githubusercontent.com/75641817/179371553-7a85d317-4034-40c2-ac64-427867238542.png)


For each domain, a subgraph of the global graph was created and Degree Centrality (DC), Closeness Centrality (CC), and Betweenness Centrality (BC) were calculated for each node in that graph. The sum of these 3 metrics is the importance score for node i. the score of an email is the sum of all node's scores that include this email in this domain. 
