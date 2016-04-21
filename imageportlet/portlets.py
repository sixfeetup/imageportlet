import logging
import urllib
from random import shuffle

from DateTime import DateTime
from zope.schema.fieldproperty import FieldProperty
from z3c.form import field
from zope import schema
from zope.interface import implements
from zope.component import getMultiAdapter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from plone.app.form.widgets.wysiwygwidget import WYSIWYGWidget
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from plone.namedfile.field import NamedImage
from plone.namedfile.interfaces import IImageScaleTraversable

import z3cformhelper  # XXX: Import from plone.app.portlets since Plone 4.3

logger = logging.getLogger('imageportlet.portlets')


def _(x):
    """ Spoof gettext for now """
    return x


class IImagePortlet(IPortletDataProvider):
    """
    Define image portlet fields.
    """

    image = NamedImage(
            title=_(u"Default Image"),
            description=_(u"Default image displayed in the portlet"),
            required=False,
        )

    headingText = schema.Text(title=_(u"Heading"),
                           description=_(u"Text on top of the default image"),
                           required=False,
                           default=u"")

    image2 = NamedImage(
            title=_(u"Rollover Image"),
            description=_(u"Image displayed when hovering over the portlet"),
            required=False,
            default=None)

    text = schema.Text(title=_(u"Rollover text"),
                       description=_(u"Text displayed when hovering over the portlet"),
                       required=False,
                       default=u"")

    link = schema.TextLine(title=_(u"Link"),
                           description=_(u"Absolute or site root relative link target"),
                           required=False,
                           default=None)

    css = schema.TextLine(title=_(u"HTML styling"),
                          description=_(u"Extra CSS classes"),
                          required=False)


class Assignment(base.Assignment):

    # We need to explicitly mark our persistant data for @@images view look-up
    implements(IImagePortlet, IImageScaleTraversable)

    # Make sure default values work correctly migration proof manner
    text = FieldProperty(IImagePortlet["text"])
    headingText = FieldProperty(IImagePortlet["headingText"])

    image = FieldProperty(IImagePortlet["image"])
    image2 = FieldProperty(IImagePortlet["image2"])
    link = FieldProperty(IImagePortlet["link"])

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def modified(self):
        """
        plone.namedfield uses this information to refresh image URLs when the content changes

        (cache busting)
        """
        return DateTime(self._p_mtime)

    @property
    def title(self):
        """
        Be smart as what show as the management interface title.
        """
        entries = [self.headingText, u"Image portlet"]
        for e in entries:
            if e:
                return e


class Renderer(base.Renderer):

    render = ViewPageTemplateFile('templates/imageportlet.pt')

    def update(self):
        """
        """
        self.imageData = self.compileImageData()

    def compileImageData(self):
        """
        Compile a list of images
        """

        data = []

        if self.data.image:
            data.append(dict(image=self.data.image, link=self.data.link, id="image"))

        # getattr -> migration safe
        if getattr(self.data, "image2", None):
            data.append(dict(image=self.data.image2, id="image2"))

        return data

    def getDefaultImage(self):
        """
        Return the first available image or None
        """
        if len(self.imageData) > 0:
            return self.imageData[0]["image"]
        return None

    def getDefaultLink(self):
        """
        Return the only link for the portlet which can be used with the header/footer text.

        If we have several images we cannot rotate these links.
        """

        if len(self.imageData) == 1:
            return self.imageData[0]["link"]

        return None

    def getAcquisitionChainedAssigment(self):
        """
        FFFFUUUUUUU Plone.
        """

        # XXX: Persistently set by now by add form
        column = getattr(self.data, "column", None)
        if column:
            # column is PortletAssignmentMapping https://github.com/plone/plone.app.portlets/blob/master/plone/app/portlets/storage.py
            # which is http://svn.zope.org/zope.container/trunk/src/zope/container/ordered.py?rev=120790&view=auto
            for key, value in column.items():
                if value == self.data:
                    return column, key, column[key]

        return None

    def getHeadingText(self):
        """
        """
        return self.data.headingText

    def getOnImageText(self):
        """
        """
        return self.data.text

    def getStyle(self, imageDesc):
        """
        Get explicity style for the image-wrapper CSS class.

        Use image width and height
        """

        image = imageDesc["image"]

        width, height = image.getImageSize()

        return "background: url(%s) no-repeat top left; width: %dpx; height: %dpx" % (self.getImageURL(imageDesc), width, height)

    def getLink(self, imageDesc):
        """
        :return: absolute transformed link or None if link not present
        """

        link = imageDesc["link"]

        if not link:
            return None

        if "//" in link:
            return link

        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')

        if link.startswith("/"):
            link = link[1:]

        return "%s/%s" % (portal_state.portal_url(), link)

    def getImageURL(self, imageDesc):
        """
        :return: The URL where the image can be downloaded from.

        """
        context = self.context.aq_inner

        if not hasattr(self, "__portlet_metadata__"):
            # XXX: Plone 3?
            import pdb ; pdb.set_trace()
            return ""

        # [{'category': 'context', 'assignment': <imageportlet.portlets.Assignment object at 0x1138bb140>, 'name': u'bound-method-assignment-title-of-assignment-at-1', 'key': '/Plone/fi'},
        params = dict(
            portletName=self.__portlet_metadata__["name"],
            portletManager=self.__portlet_metadata__["manager"],
            image=imageDesc["id"],
            modified=self.data._p_mtime,
            portletKey=self.__portlet_metadata__["key"],
        )

        imageURL = "%s/@@image-portlet-downloader?%s" % (context.absolute_url(), urllib.urlencode(params))

        return imageURL

    def getCarouselCSSClass(self):
        """
        """

        if len(self.imageData) > 1:
            # Referred in JS
            cls = "image-portlet-carousel"
        else:
            cls = "image-portlet-no-carousel"
        return cls

    def getPortletCSSClass(self):
        """
        """
        cls = ""

        if self.getOnImageText():
            cls += " image-portlet-text"
        else:
            cls += " image-portlet-no-text"

        if self.data.css:
            cls += self.data.css

        return cls

    def getWrapperStyle(self):
        """
        Allocate pixel spaces to show all carousel images, so no jumpy pages
        """
        max_width = 0
        max_height = 0

        for imageDesc in self.data.imageData:
            size = imageDesc["image"].getImageSize()
            max_width = max(size[0], max_width)
            max_height = max(size[1], max_height)

        return "width: %dpx; height: %dpx" % (max_width, max_height)
        
    def transformed(self, mt='text/x-html-safe'):
        """Use the safe_html transform to protect text output. This also
        ensures that resolve UID links are transformed into real links.
        """
        orig = self.data.text
        context = aq_inner(self.context)
        if not isinstance(orig, unicode):
            # Apply a potentially lossy transformation, and hope we stored
            # utf-8 text. There were bugs in earlier versions of this portlet
            # which stored text directly as sent by the browser, which could
            # be any encoding in the world.
            orig = unicode(orig, 'utf-8', 'ignore')
            logger.warn("Static portlet at %s has stored non-unicode text. "
                        "Assuming utf-8 encoding." % context.absolute_url())

        # Portal transforms needs encoded strings
        orig = orig.encode('utf-8')

        transformer = getToolByName(context, 'portal_transforms')
        data = transformer.convertTo(mt, orig,
                                     context=context, mimetype='text/html')
        result = data.getData()
        if result:
            return unicode(result, 'utf-8')
        return None


class AddForm(z3cformhelper.AddForm):

    fields = field.Fields(IImagePortlet)
    fields['headingText'].custom_widget = WYSIWYGWidget
    fields['text'].custom_widget = WYSIWYGWidget

    def create(self, data):
        return Assignment(**data)


class EditForm(z3cformhelper.EditForm):

    fields = field.Fields(IImagePortlet)
    fields['headingText'].custom_widget = WYSIWYGWidget
    fields['text'].custom_widget = WYSIWYGWidget
