from rubicon.objc import SEL, objc_method, objc_property
from travertino.size import at_least

from toga_cocoa.containers import Container
from toga_cocoa.libs import (
    NSColor,
    NSMakePoint,
    NSMakeRect,
    NSNoBorder,
    NSNotificationCenter,
    NSRunLoop,
    NSScrollView,
    NSScrollViewDidEndLiveScrollNotification,
    NSScrollViewDidLiveScrollNotification,
)

from .base import Widget


class TogaScrollView(NSScrollView):
    interface = objc_property(object, weak=True)
    impl = objc_property(object, weak=True)

    @objc_method
    def didScroll_(self, note) -> None:
        self.interface.on_scroll(None)


class ScrollContainer(Widget):
    def create(self):
        self.native = TogaScrollView.alloc().init()
        self.native.interface = self.interface
        self.native.impl = self

        self.native.autohidesScrollers = True
        self.native.borderType = NSNoBorder
        self.native.backgroundColor = NSColor.windowBackgroundColor

        # The container for the document bases its layout on the
        # size of the content view. It can only exceed the size
        # of the contentView if scrolling is enabled in that axis.
        self.document_container = Container(
            layout_native=self.native.contentView,
            on_refresh=self.content_refreshed,
        )
        self.native.documentView = self.document_container.native

        NSNotificationCenter.defaultCenter.addObserver(
            self.native,
            selector=SEL("didScroll:"),
            name=NSScrollViewDidLiveScrollNotification,
            object=self.native,
        )
        NSNotificationCenter.defaultCenter.addObserver(
            self.native,
            selector=SEL("didScroll:"),
            name=NSScrollViewDidEndLiveScrollNotification,
            object=self.native,
        )

        # Add the layout constraints
        self.add_constraints()

    def set_content(self, widget):
        # If there's existing content, clear its container
        if self.interface.content:
            self.interface.content._impl.container = None

        # If there's new content, set the container of the content
        if widget:
            widget.container = self.document_container

    def set_bounds(self, x, y, width, height):
        super().set_bounds(x, y, width, height)

        # Setting the bounds changes the constraints, but that doesn't mean
        # the constraints have been fully applied. Let the NSRunLoop tick once
        # to ensure constraints are applied.
        NSRunLoop.currentRunLoop.runUntilDate(None)

        # Now that we have an updated size for the ScrollContainer, re-evaluate
        # the size of the document content
        if self.interface._content:
            self.interface._content.refresh()

    def content_refreshed(self):
        width = self.native.frame.size.width
        height = self.native.frame.size.height

        if self.interface.horizontal:
            width = max(self.interface.content.layout.width, width)

        if self.interface.vertical:
            height = max(self.interface.content.layout.height, height)

        self.native.documentView.frame = NSMakeRect(0, 0, width, height)

    def get_vertical(self):
        return self.native.hasVerticalScroller

    def set_vertical(self, value):
        self.native.hasVerticalScroller = value
        # If the scroll container has content, we need to force a refresh
        # to let the scroll container know how large it's content is.
        if self.interface.content:
            self.interface.refresh()

    def get_horizontal(self):
        return self.native.hasHorizontalScroller

    def set_horizontal(self, value):
        self.native.hasHorizontalScroller = value
        # If the scroll container has content, we need to force a refresh
        # to let the scroll container know how large it's content is.
        if self.interface.content:
            self.interface.refresh()

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)

    def get_max_vertical_position(self):
        return max(
            0,
            self.native.documentView.bounds.size.height
            - self.native.contentView.bounds.size.height,
        )

    def get_vertical_position(self):
        return self.native.contentView.bounds.origin.y

    def set_vertical_position(self, vertical_position):
        if vertical_position < 0:
            vertical_position = 0
        else:
            max_value = self.get_max_vertical_position()
            if vertical_position > max_value:
                vertical_position = max_value

        new_position = NSMakePoint(
            self.native.contentView.bounds.origin.x,
            vertical_position,
        )
        self.native.contentView.scrollToPoint(new_position)
        self.native.reflectScrolledClipView(self.native.contentView)
        self.interface.on_scroll(None)

    def get_max_horizontal_position(self):
        return max(
            0,
            self.native.documentView.bounds.size.width
            - self.native.contentView.bounds.size.width,
        )

    def get_horizontal_position(self):
        return self.native.contentView.bounds.origin.x

    def set_horizontal_position(self, horizontal_position):
        if horizontal_position < 0:
            horizontal_position = 0
        else:
            max_value = self.get_max_horizontal_position()
            if horizontal_position > max_value:
                horizontal_position = max_value

        new_position = NSMakePoint(
            horizontal_position,
            self.native.contentView.bounds.origin.y,
        )
        self.native.contentView.scrollToPoint(new_position)
        self.native.reflectScrolledClipView(self.native.contentView)
        self.interface.on_scroll(None)
