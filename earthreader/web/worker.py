""":mod:`earthreader.web.worker` --- Crawl worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import threading
from six.moves import queue

from libearth.crawler import CrawlError, crawl


class Worker(object):
    """Crawl worker."""

    def __init__(self, app):
        self.crawling_queue = queue.Queue()
        self.worker = threading.Thread(target=self.crawl_category)
        self.worker.setDaemon(True)
        self.worker_num = app.config.get('CRAWLER_THREAD', 4)

    def start_worker(self):
        if not self.worker.isAlive():
            try:
                self.worker.start()
            except RuntimeError:
                self.worker = threading.Thread(target=self.crawl_category)
                self.worker.setDaemon(True)
                self.worker.start()

    def kill_worker(self):
        if self.worker.isAlive():
            self.crawling_queue.put((0, 'terminate'))
            self.worker.join()

    def is_running(self):
        return self.worker.isAlive()

    def add_job(self, cursor, feed_id):
        self.crawling_queue.put((1, (cursor, feed_id)))

    def empty_queue(self):
        with self.crawling_queue.mutex:
            self.crawling_queue.queue.clear()

    def qsize(self):
        return self.crawling_queue.qsize()

    def crawl_category(self):
        running = True
        while running:
            priority, arguments = self.crawling_queue.get()
            if priority == 0:
                if arguments == 'terminate':
                    running = False
                self.crawling_queue.task_done()
            elif priority == 1:
                cursor, feed_id = arguments
                urls = {}
                if not feed_id:
                    urls = dict((sub.feed_uri, sub.feed_id)
                                for sub in cursor.recursive_subscriptions)
                else:
                    urls = dict((sub.feed_uri, sub.feed_id)
                                for sub in cursor.recursive_subscriptions
                                if sub.feed_id == feed_id)
                iterator = iter(crawl(urls, self.worker_num))
                while True:
                    try:
                        feed_url, feed_data, crawler_hints = next(iterator)
                        with get_stage() as stage:
                            stage.feeds[urls[feed_url]] = feed_data
                    except CrawlError:
                        continue
                    except StopIteration:
                        break
                self.crawling_queue.task_done()
