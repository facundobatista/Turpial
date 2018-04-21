# -*- coding: utf-8 -*-

# Qt widget to show statusesin Turpial using a QWebView

import re
import os

from jinja2 import Template

from PyQt4.QtWebKit import QWebView
from PyQt4.QtWebKit import QWebPage
from PyQt4.QtWebKit import QWebSettings

from PyQt4.QtCore import Qt
from PyQt4.QtCore import pyqtSignal

from turpial.ui.lang import i18n
from libturpial.common import is_preview_service_supported


class StatusesWebView(QWebView):

    link_clicked = pyqtSignal(str)
    hashtag_clicked = pyqtSignal(str)
    profile_clicked = pyqtSignal(str)
    cmd_clicked = pyqtSignal(str)

    EMPTY_PAGE = '<html><head></head><body></body></html>'

    def __init__(self, base, column_id):
        QWebView.__init__(self)
        self.base = base
        self.column_id = column_id
        self.linkClicked.connect(self.__element_clicked)
        page = self.page()
        page.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        page.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        if not self.base.debug:
            self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setPage(page)
        self.setHtml(self.EMPTY_PAGE)

        self.status_template = self.__load_template('status.html')
        self.load_style()

        self.show()

    def __element_clicked(self, qurl):
        try:
            url = str(qurl.toString())
        except UnicodeEncodeError:
            return

        if url.startswith('http'):
            self.link_clicked.emit(url)
        elif url.startswith('hashtag'):
            hashtag = "#%s" % url.split(':')[2]
            self.hashtag_clicked.emit(hashtag)
        elif url.startswith('profile'):
            self.profile_clicked.emit(url.split(':')[1])
        elif url.startswith('cmd'):
            self.cmd_clicked.emit(url.split('cmd:')[1])

    def __load_template(self, name):
        path = os.path.join(self.base.templates_path, name)
        fd = open(path)
        content = fd.read()
        fd.close()
        return Template(content)

    def __load_stylesheet(self):
        attrs = {
            'mark_protected': os.path.join(self.base.images_path, 'mark-protected.png'),
            'mark_favorited': os.path.join(self.base.images_path, 'mark-favorited2.png'),
            'mark_repeated': os.path.join(self.base.images_path, 'mark-repeated2.png'),
            'mark_reposted': os.path.join(self.base.images_path, 'mark-reposted.png'),
            'mark_verified': os.path.join(self.base.images_path, 'mark-verified.png'),
            'action_reply': os.path.join(self.base.images_path, 'action-reply.png'),
            'action_reply_direct': os.path.join(self.base.images_path, 'action-reply-direct.png'),
            'action_repeat': os.path.join(self.base.images_path, 'action-repeat.png'),
            'action_quote': os.path.join(self.base.images_path, 'action-quote.png'),
            'action_favorite': os.path.join(self.base.images_path, 'action-favorite.png'),
            'action_reply_shadowed': os.path.join(
                self.base.images_path, 'action-reply-shadowed.png'),
            'action_reply_direct_shadowed': os.path.join(
                self.base.images_path, 'action-reply-direct-shadowed.png'),
            'action_repeat_shadowed': os.path.join(
                self.base.images_path, 'action-repeat-shadowed.png'),
            'action_quote_shadowed': os.path.join(
                self.base.images_path, 'action-quote-shadowed.png'),
            'action_favorite_shadowed': os.path.join(
                self.base.images_path, 'action-favorite-shadowed.png'),
            'action_delete': os.path.join(self.base.images_path, 'action-delete.png'),
            'action_delete_shadowed': os.path.join(
                self.base.images_path, 'action-delete-shadowed.png'),
            'scrollbar_background_color': self.base.theme['scrollbar']['background_color'],
            'scrollbar_border_color': self.base.theme['scrollbar']['border_color'],
            'scrollbar_handler_color': self.base.theme['scrollbar']['handler_color'],
            'status_background_color': self.base.theme['status']['background_color'],
            'quote_background_color': self.base.theme['status']['quote_background_color'],
            'status_border_color': self.base.theme['status']['border_color'],
            'status_text_color': self.base.theme['status']['text_color'],
            'username_text_color': self.base.theme['status']['username']['text_color'],
            'username_hover_text_color': self.base.theme['status']['username']['hover_text_color'],
            'entities_text_color': self.base.theme['entities']['text_color'],
            'entities_hover_text_color': self.base.theme['entities']['hover_text_color'],
            'footer_text_color': self.base.theme['footer']['text_color'],
            'footer_hover_text_color': self.base.theme['footer']['hover_text_color'],
            'conversation_background_color': self.base.theme['conversation']['background_color'],
            'message_font_size': self.base.get_message_font_size(),
            'footer_font_size': self.base.get_footer_font_size(),
            'alert_font_size': self.base.get_alert_font_size(),
            'username_font_size': self.base.get_username_font_size(),
        }
        stylesheet = self.__load_template('style.css')
        return stylesheet.render(attrs)

    def __render_status(self, status, with_conversation=True):
        repeated_by = None
        conversation_id = None
        view_conversation = None
        hide_conversation = None
        message = status.text
        message = message.replace('\n', '<br/>')
        message = message.replace('\'', '&apos;')
        timestamp = self.base.humanize_timestamp(status.timestamp)
        timestamp = timestamp.replace(' ', '')
        quote_username = None
        quote_message = None

        media = []
        if status.entities:
            # Highlight URLs
            for url in status.entities['urls']:
                pretty_url = "<a href='%s' title='%s'>%s</a>" % (
                    url.url, url.url, url.display_text)
                message = message.replace(url.search_for, pretty_url)

                # Removed inline preview for instagram
                if is_preview_service_supported(url.url) and self.base.core.get_inline_preview():
                    if url.url.find('instagram') < 0:
                        media.append(url.url)

                if status.is_quote_status and hasattr(status.quoted_status, 'username'):
                    quote_username = status.quoted_status.username
                    quote_message = status.quoted_status.text

            # Highlight hashtags
            for hashtag in status.entities['hashtags']:
                pretty_hashtag = "<a href='hashtag:%s:%s'>%s</a>" % (
                    hashtag.account_id, hashtag.display_text[1:], hashtag.display_text)
                pattern = r"%s\b" % hashtag.search_for
                message = re.sub(pattern, pretty_hashtag, message)

            # Highlight mentions
            for mention in status.entities['mentions']:
                pretty_mention = "<a href='profile:%s'>%s</a>" % (
                    mention.url, mention.display_text)
                message = message.replace(mention.search_for, pretty_mention)

        if status.repeated_by:
            repeated_by = "%s %s" % (i18n.get('retweeted_by'), status.repeated_by)
        if status.in_reply_to_id and with_conversation:
            conversation_id = "%s-conversation-%s" % (self.column_id, status.id_)
            view_conversation = i18n.get('view_conversation')
            hide_conversation = i18n.get('hide_conversation')

        if self.base.core.get_show_user_avatars():
            avatar = status.avatar
        else:
            avatar = "file://%s" % os.path.join(self.base.images_path, 'unknown.png')

        attrs = {
            'status': status,
            'message': message,
            'repeated_by': repeated_by,
            'timestamp': timestamp,
            'view_conversation': view_conversation,
            'reply': i18n.get('reply'),
            'hide_conversation': hide_conversation,
            'quote': i18n.get('quote'),
            'retweet': i18n.get('retweet'),
            'mark_as_favorite': i18n.get('mark_as_favorite'),
            'delete': i18n.get('delete'),
            'remove_from_favorites': i18n.get('remove_from_favorites'),
            'conversation_id': conversation_id,
            'in_progress': i18n.get('in_progress'),
            'loading': i18n.get('loading'),
            'avatar': avatar,
            'media': media,
            'quote_username': quote_username,
            'quote_message': quote_message,
        }

        return self.status_template.render(attrs)

    def update_statuses(self, statuses):
        statuses_ = statuses[:]
        content = ''

        current_page = self.page().currentFrame().toHtml()

        if current_page == self.EMPTY_PAGE or current_page == '':
            for status in statuses_:
                content += self.__render_status(status)
            column = self.__load_template('column.html')
            args = {
                'stylesheet': self.stylesheet,
                'content': content,
                'favorite_tooltip': i18n.get('mark_as_favorite'),
                'unfavorite_tooltip': i18n.get('remove_from_favorites'),
            }
            html = column.render(args)

            fd = open('/tmp/turpial-debug.html', 'w')
            fd.write(html.encode('ascii', 'ignore'))
            fd.close()
            self.setHtml(html)
            self.clear_new_marks()
        else:
            statuses_.reverse()
            for status in statuses_:
                content = self.__render_status(status)
                self.append_status(content, status.id_)
            self.execute_javascript('restoreScrollPosition()')

    def clear(self):
        self.setHtml(self.EMPTY_PAGE)

    def execute_javascript(self, js_cmd):
        self.page().mainFrame().evaluateJavaScript(js_cmd)

    def update_conversation(self, status, status_root_id):
        status_rendered = self.__render_status(status, with_conversation=False)
        status_rendered = status_rendered.replace("\n", '')
        status_rendered = status_rendered.replace('\'', '"')
        conversation = """updateConversation('%s', '%s')""" % (status_root_id, status_rendered)
        self.execute_javascript(conversation)

    def view_conversation(self, status_root_id):
        conversation = "viewConversation('%s')" % status_root_id
        self.execute_javascript(conversation)

    def clear_conversation(self, status_root_id):
        conversation = "clearConversation('%s')" % status_root_id
        self.execute_javascript(conversation)

    def append_status(self, html, status_id):
        html = html.replace("\n", '')
        html = html.replace('\'', '"')

        fd = open('/tmp/turpial-update-column.html', 'w')
        fd.write(html.encode('ascii', 'ignore'))
        fd.close()

        cmd = """appendStatus('%s', '%s')""" % (html, status_id)
        self.execute_javascript(cmd)

    def sync_timestamps(self, statuses):
        for status in statuses:
            new_timestamp = self.base.humanize_timestamp(status.timestamp)
            full_url = '<a href="cmd:details_menu:{}">{}</a>'.format(status.id_, new_timestamp)
            cmd = """updateTimestamp('%s', '%s')""" % (status.id_, full_url)
            self.execute_javascript(cmd)

    def clear_new_marks(self):
        self.execute_javascript("clearNewMarks()")

    def load_style(self):
        self.stylesheet = self.__load_stylesheet()
        self.setStyleSheet(
            "QWidget { background-color: %s}" % self.base.theme['status']['background_color'])
