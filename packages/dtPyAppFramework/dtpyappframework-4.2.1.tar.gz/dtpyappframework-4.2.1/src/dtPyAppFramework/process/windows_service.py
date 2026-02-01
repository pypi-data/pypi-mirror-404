import platform
import logging
import sys

if platform.system() == "Windows":
    try:
        import win32service
        import socket
        import win32serviceutil
        import win32event
        import servicemanager
    except ImportError as ex:
        logging.error("pywin32 is not installed.")
        raise ex


class WindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = None
    _svc_display_name_ = None
    _svc_description_ = None
    _running_function_ = None
    _stop_function_ = None

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.args = args

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self._stop_function_()

    def SvcDoRun(self):
        try:
            rc = None
            logging.info(f"Service {self._svc_name_} is starting...")
            self._running_function_(self.args)
            while rc != win32event.WAIT_OBJECT_0:
                rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
        except Exception as ex:
            logging.exception(str(ex))
            print(str(ex))
            raise ex
        logging.info(f"Service {self._svc_name_} is stopping...")

def call_service(svc_name, svc_display_name, svc_description, main_function, exit_function):
    WindowsService._svc_name_ = svc_name
    WindowsService._svc_display_name_ = svc_display_name
    WindowsService._svc_description_ = svc_description
    WindowsService._running_function_ = main_function
    WindowsService._stop_function_ = exit_function

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(WindowsService)
