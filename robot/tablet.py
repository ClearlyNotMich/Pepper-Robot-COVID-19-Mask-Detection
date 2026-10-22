"""Tablet wrapper using an explicitly configured deployment URL."""
from __future__ import print_function


class Tablet(object):
    def __init__(self, session, website_url):
        self.session = session
        self.website_url = website_url
        self.tablet_service = session.service("ALTabletService")

    def show_website(self):
        self.tablet_service.enableWifi()
        self.tablet_service.showWebview(self.website_url)

    def hide_website(self):
        self.tablet_service.hideWebview()
