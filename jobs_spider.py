import scrapy
from scrapy import http
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule, CrawlSpider, Spider
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import nltk, re
from nltk.corpus import stopwords
import subject_extraction, trigram_tagger
from subject_extraction import extract_subject, tag_sentences, get_svo


class JobsSpider(Spider):
    name="jobs"
    start_urls = ['https://www.indeed.com/q-machine-learning-l-Austin,-TX-jobs.html']

    def parse(self, response):
        base_website = "http://indeed.com"
        job_links = response.xpath('//td[@id="resultsCol"]//h2//a')
        job_next_page = response.xpath('//td[@id="resultsCol"]//div[@class="pagination"]//a/@href')[-1].extract()

        for index, job in enumerate(job_links):
            job_link = base_website + job.xpath('@href').extract_first()
            request = scrapy.Request(job_link, self.parse_item)
            request.meta['job_link']  = job_link
            request.meta['title'] = job.xpath('@title').extract_first()

            yield request

        if job_next_page is not None:
            yield response.follow(job_next_page, self.parse)

    def parse_item(self, response):
         yield {
            'title': response.meta['title'],
            'job_link': response.url,
            'description': self.get_job_description(response)
         }

    def get_job_description(self, response):

        soup_obj = BeautifulSoup(response.text, "lxml")  # Get the html from the site

        for script in soup_obj(["script", "style"]):
            script.extract()  # Remove these two elements from the BS4 object

        text = soup_obj.get_text()  # Get the text from this

        lines = (line.strip() for line in text.splitlines())  # break into lines

        chunks = (phrase.strip() for line in lines for phrase in
                  line.split("  "))  # break multi-headlines into a line each

        def chunk_space(chunk):
            chunk_out = chunk + ' '  # Need to fix spacing issue
            return chunk_out

        text = ''.join(chunk_space(chunk) for chunk in chunks if chunk).encode('utf-8')  # Get rid of all blank lines and ends of line

        # Now clean out all of the unicode junk (this line works great!!!)

        try:
            text = text.decode('unicode_escape').encode('ascii', 'ignore')  # Need this as some websites aren't formatted
        except:  # in a way that this works, can occasionally throw
            return  # an exception

        text = re.sub("[^a-zA-Z.+3]", " ", text)  # Now get rid of any terms that aren't words (include 3 for d3.js)
        # Also include + for C++

        text = text.lower().split()  # Go to lower case and split them apart

        stop_words = set(stopwords.words("english"))  # Filter out any stop words
        text = [w for w in text if not w in stop_words]

        text = list(set(text))  # Last, just get the set of these. Ignore counts (we are just looking at whether a term existed
        # or not on the website)

        return ' '.join(text)