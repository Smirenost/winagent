import argparse
import queue
import threading
import os
from time import sleep
import multiprocessing


if __name__ == "__main__":

    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Tactical RMM Windows Agent")
    parser.add_argument("-m", action="store", dest="mode", type=str)
    parser.add_argument("-p", action="store", dest="taskpk", type=int)
    args = parser.parse_args()

    if args.mode == "winagentsvc":
        from winagentsvc import WinAgentSvc

        agent = WinAgentSvc()
        agent.run()
    elif args.mode == "checkrunner":
        from checkrunner import CheckRunner

        agent = CheckRunner()
        agent.run_forever()
    elif args.mode == "runchecks":
        from checkrunner import CheckRunner

        agent = CheckRunner()
        agent.run()
    elif args.mode == "winupdater":
        from winupdater import WinUpdater

        agent = WinUpdater()
        agent.install_all()

    elif args.mode == "patchscan":
        from winupdater import WinUpdater

        agent = WinUpdater()
        agent.trigger_patch_scan()

    elif args.mode == "taskrunner":
        from taskrunner import TaskRunner

        agent = TaskRunner(task_pk=args.taskpk)
        agent.run()

    elif args.mode == "updatesalt":
        from agent import WindowsAgent

        agent = WindowsAgent()
        agent.update_salt()
    elif args.mode == "cleanup":
        from agent import WindowsAgent

        agent = WindowsAgent()
        agent.cleanup()
    else:
        import PySimpleGUI as sg
        import psutil
        import ctypes

        if not ctypes.windll.shell32.IsUserAnAdmin():
            sg.ChangeLookAndFeel("Reddit")
            sg.Popup("Must be run as administrator!")
            raise SystemExit()

        try:
            service = psutil.win_service_get("tacticalagent")
        except psutil.NoSuchProcess:

            gui_queue = queue.Queue()

            sg.SetOptions(
                font=("Helvetica", 12), icon=os.path.join(os.getcwd(), "onit.ico")
            )
            sg.ChangeLookAndFeel("Reddit")
            layout = [
                [sg.Output(size=(50, 12))],
                [sg.Button("Close", key="exit", visible=False)],
            ]

            window = (
                sg.Window("Tactical RMM", disable_close=True,).Layout(layout).Finalize()
            )
            window.Hide()  # hack to run in main thread and run the install in background thread so tkinter doesn't crash

            started = True
            while 1:
                event, values = window.Read(timeout=100)
                if event is None:
                    pass

                elif started:
                    try:
                        from installer import Installer

                        install = Installer()
                        install.pre_install()
                        window.UnHide()
                        threading.Thread(
                            target=install.install_all, args=(gui_queue,), daemon=True
                        ).start()
                        started = False

                    except Exception as e:
                        print(e)
                    finally:
                        started = False

                elif event == "exit":
                    break

                try:
                    message = gui_queue.get_nowait()
                except queue.Empty:
                    message = None

                if (
                    message != "installfinished"
                    and message != "installerror"
                    and message != None
                ):
                    print(message)

                if message == "installfinished" or message == "installerror":
                    window.Element("exit").Update(visible=True)

            window.Close()
        else:
            from installer import AgentGUI

            agent = AgentGUI()
            agent.show_status()
