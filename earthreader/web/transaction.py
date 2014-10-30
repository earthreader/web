""":mod:`earthreader.web.transaction` --- Transact subscriptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from libearth.subscribe import SubscriptionList

from .exceptions import InvalidCategoryID, FeedNotFound
from .stage import stage


class SubscriptionTransaction(object):
    """Transaction manager to manage changes of subscriptions.
    To save changes occurred in a subscription list,
    the outlines which are target of the changes must be derived from a single
    :class:`libearth.subscribe.SubscriptionList`, and save the list to
    the stage. You can get outlines through an instance of this class,
    and save the changes.
    """

    def __init__(self):
        with stage:
            self.subscriptions = (stage.subscriptions if stage.subscriptions
                                  else SubscriptionList())
        self.feeds_updated = {}

    def get_feed(self, feed_id, category_id=None):
        if category_id:
            self.get_category(category_id)
        try:
            with stage:
                return stage.feeds[feed_id]
        except KeyError:
            raise FeedNotFound

    def add_feed(self, category, feed):
        subscription = category.subscribe(feed)
        self.feeds_updated[subscription.feed_id] = feed

    def update_feed(self, feed_id, feed):
        self.feeds_updated[feed_id] = feed

    def get_parent_category(self, category_id):
        parent_category_path = self.get_path(category_id)[:-1]
        return self.get_category_using_path(parent_category_path)

    def get_category(self, category_id):
        return self.get_category_using_path(self.get_path(category_id))

    def get_category_using_path(self, category_path):
        category = self.subscriptions
        for key in category_path:
            try:
                category = category.categories[key]
            except KeyError:
                raise InvalidCategoryID('The given category ID is not valid')
        return category

    def get_path(self, category_id):
        if not category_id:
            return []
        return [key[1:] for key in category_id.split('/')]

    def save(self):
        with stage:
            stage.subscriptions = self.subscriptions
            for feed_id, feed in self.feeds_updated.items():
                stage.feeds[feed_id] = feed
            self.subscriptions = stage.subscriptions
