#!/usr/bin/env python2.7
#@HEADER
###############################################################################
PNGViewer_module_aliases = {}
for m in [
    "bcolors",
    "os",
    "sys",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in PNGViewer_module_aliases:
            globals()[PNGViewer_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False
try:
    import paraview.simple as pv
    globals()["has_paraview"] = True
except:
    globals()["has_paraview"] = False
    if not __name__ == '__main':
        print("[PNGViewer] Failed to import paraview. Cannot save visual artifacts.")
        sys.exit(0)
from ParaviewViewer    import ParaviewViewer

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ParaviewViewerBase     import ViewerParameters
        from ParaviewViewerBase     import ParaviewViewerBase
    else:
        from ..ParaviewViewerBase   import ViewerParameters
        from ..ParaviewViewerBase   import ParaviewViewerBase

###############################################################################
class PNGViewer(ParaviewViewer):
    """A concrete class providing a PNG Viewer
    """

    ###########################################################################
    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super(PNGViewer, self).__init__(exodus, file_name, viewer_type)

    ###########################################################################
    def saveView(self, reader):
        """Save figure
        """

        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        print(bcolors.HEADER
            + "[PNGViewer] "
            + bcolors.END
            + "###  Generating PNG images...")
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t
            pv.WriteImage(self.file_name + ".%f.png" % t);
        print(bcolors.HEADER
            + "[PNGViewer] "
            + bcolors.END
            + "### All PNG images generated.")

###############################################################################
if __name__ == '__main__':

    # Check if visualization library imported
    if not has_paraview:
        print(bcolors.ERR
            + "** ERROR: failed to import paraview. Cannot save visual artifacts.Exiting."
            + bcolors.END)
        sys.exit(1)

    # Print startup information
    sv = sys.version_info
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "Parsing command line arguments")
    params = ViewerParameters()
    if params.parse_command_line():
        sys.exit(1)
    pngViewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "PNG")

    # Create view from PNGViewer instance
    reader = pngViewer.createViews()

    # Save generated view
    pngViewer.saveView(reader)

    # If this point is reached everything went fine
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "{} file views generated ###".format(pngViewer.file_name))

###############################################################################
