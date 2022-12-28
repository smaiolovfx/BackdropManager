from BackdropManager import backdrop_manager, info

try:
    backdrop_manager.nuke_setup()
except Exception:
    import traceback
    traceback.print_exc() 
