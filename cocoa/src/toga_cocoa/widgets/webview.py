from rubicon.objc import objc_method, objc_property, py_from_ns
from rubicon.objc.runtime import objc_id
from travertino.size import at_least

from toga.widgets.webview import JavaScriptResult

from ..libs import NSURL, NSURLRequest, WKWebView
from .base import Widget


def js_completion_handler(future, on_result=None):
    def _completion_handler(res: objc_id, error: objc_id) -> None:
        if error:
            error = py_from_ns(error)
            exc = RuntimeError(str(error))
            future.set_exception(exc)
            if on_result:
                on_result(None, exception=exc)
        else:
            result = py_from_ns(res)
            future.set_result(result)
            if on_result:
                on_result(result)

    return _completion_handler


class TogaWebView(WKWebView):
    interface = objc_property(object, weak=True)
    impl = objc_property(object, weak=True)

    @objc_method
    def webView_didFinishNavigation_(self, navigation) -> None:
        self.interface.on_webview_load(self.interface)

        if self.impl.loaded_future:
            self.impl.loaded_future.set_result(None)
            self.impl.loaded_future = None

    @objc_method
    def acceptsFirstResponder(self) -> bool:
        return True


class WebView(Widget):
    def create(self):
        self.native = TogaWebView.alloc().init()
        self.native.interface = self.interface
        self.native.impl = self

        self.native.navigationDelegate = self.native
        self.native.uIDelegate = self.native

        self.loaded_future = None

        # Add the layout constraints
        self.add_constraints()

    def get_url(self):
        url = str(self.native.URL)
        return None if url == "about:blank" else url

    def set_url(self, value, future=None):
        if value:
            request = NSURLRequest.requestWithURL(NSURL.URLWithString(value))
        else:
            request = NSURLRequest.requestWithURL(NSURL.URLWithString("about:blank"))

        self.loaded_future = future
        self.native.loadRequest(request)

    def set_content(self, root_url, content):
        self.native.loadHTMLString(content, baseURL=NSURL.URLWithString(root_url))

    def get_user_agent(self):
        return str(self.native.valueForKey("userAgent"))

    def set_user_agent(self, value):
        self.native.customUserAgent = value

    def evaluate_javascript(self, javascript: str, on_result=None) -> str:
        result = JavaScriptResult()
        self.native.evaluateJavaScript(
            javascript,
            completionHandler=js_completion_handler(
                future=result.future,
                on_result=on_result,
            ),
        )

        return result

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)
