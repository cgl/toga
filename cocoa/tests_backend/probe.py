import asyncio
from ctypes import c_void_p

from rubicon.objc import SEL, NSArray, NSObject, ObjCClass, objc_method
from rubicon.objc.api import NSString

from toga.fonts import CURSIVE, FANTASY, MONOSPACE, SANS_SERIF, SERIF, SYSTEM
from toga_cocoa.libs.appkit import appkit

NSRunLoop = ObjCClass("NSRunLoop")
NSRunLoop.declare_class_property("currentRunLoop")
NSDefaultRunLoopMode = NSString(c_void_p.in_dll(appkit, "NSDefaultRunLoopMode"))


class EventListener(NSObject):
    @objc_method
    def init(self):
        self.event = asyncio.Event()
        return self

    @objc_method
    def onEvent(self):
        self.event.set()
        self.event.clear()


class BaseProbe:
    def __init__(self):
        self.event_listener = EventListener.alloc().init()

    async def post_event(self, event, delay=None):
        self.window._impl.native.postEvent(event, atStart=False)

        if delay:
            # Some widgets enter an internal runloop when processing certain events;
            # this prevents
            await asyncio.sleep(delay)
        else:
            # Add another event to the queue behind the original event, to notify us once
            # it's been processed.
            NSRunLoop.currentRunLoop.performSelector(
                SEL("onEvent"),
                target=self.event_listener,
                argument=None,
                order=0,
                modes=NSArray.arrayWithObject(NSDefaultRunLoopMode),
            )
            await self.event_listener.event.wait()

    def assert_font_family(self, expected):
        assert self.font.family == {
            CURSIVE: "Apple Chancery",
            FANTASY: "Papyrus",
            MONOSPACE: "Courier New",
            SANS_SERIF: "Helvetica",
            SERIF: "Times",
            SYSTEM: ".AppleSystemUIFont",
        }.get(expected, expected)

    async def redraw(self, message=None, delay=None):
        """Request a redraw of the app, waiting until that redraw has completed."""
        if self.app.run_slow:
            # If we're running slow, wait for a second
            print("Waiting for redraw" if message is None else message)
            delay = 1

        if delay:
            await asyncio.sleep(delay)
        else:
            # Running at "normal" speed, we need to release to the event loop
            # for at least one iteration. `runUntilDate:None` does this.
            NSRunLoop.currentRunLoop.runUntilDate(None)
