#!/usr/bin/env python
"""
Matplotlib frontend program for use in CUI env
python 3.6 based, not compatible with python2.7
"""
##########
# Import #
##########
import os, sys, glob
import subprocess
import re # Regular expression
import argparse
import yaml
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

#########
# Table #
#########
# This is 8-color scheme from colorbrewer as RGB.
__table8_colorbrewer = [
    (228,  26,  28), ( 55, 126, 184), ( 77, 175,  74), (152,  78, 163),
    (255, 127,   0), (255, 255,  51), (166,  86,  40), (247, 129, 191)]
# These are the "Tableau 20" colors as RGB.
__tableau20 = [
    ( 31, 119, 180), (174, 199, 232), (255, 127,  14), (255, 187, 120),
    ( 44, 160,  44), (152, 223, 138), (214,  39,  40), (255, 152, 150),
    (148, 103, 189), (197, 176, 213), (140,  86,  75), (196, 156, 148),
    (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
    (188, 189,  34), (219, 219, 141), ( 23, 190, 207), (158, 218, 229)]

# Scale the RGB values to [0, 1] range, which is the format that matplotlib accepts.
__colorTable = []
for one_color in __table8_colorbrewer + __tableau20:
    r, g, b = one_color
    __colorTable.append((r / 255., g / 255., b / 255.))
__nColorTable = len(__colorTable)

############
# Function #
############
def makePlot(conf):
    """
    TODO list:
        enable 2 y-axis graph
    """
    #################
    ## Preparation ##
    #################
    # Variable Aliases
    Figure  = conf.get("Figure")
    Font    = conf.get("Font")
    Preset  = conf["Preset"]
    Default = conf["Preset"]["Default"]
    Case    = conf["Case"]
    Legend  = conf.get("Legend")
    Scatter = conf.get("Scatter")
    Text    = conf.get("Text")

    # Set plot attribute
    fig, ax = plt.subplots()
    fig.set_figwidth(Figure["width"]/Figure["dpi"])
    fig.set_figheight(Figure["height"]/Figure["dpi"])
    fig.set_dpi(Figure["dpi"])

    ax.spines["top"].set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.spines["right"].set_visible(True)
    ax.spines["left"].set_visible(True)

    plt.alpha=1.0

    # latex font is not fully applicable
    # discourage use of latex over mathtext
    mpl.rcParams['text.usetex'] = False
    mpl.rcParams['text.latex.unicode'] = False
    mpl.rcParams['mathtext.fontset'] = 'cm'

    # Set font
    font_prop={}
    for key in Font:
        font_prop[key] = mpl.font_manager.FontProperties(
            family =Font[key].get("family"),
            size   =Font[key].get("size"),
            weight =Font[key].get("weight"),
            style  =Font[key].get("style"),
            variant=Font[key].get("variant"),
            stretch=Font[key].get("stretch"))

    all_font_items = (
        [ax.title, ax.xaxis.label, ax.yaxis.label]
        + ax.get_xticklabels()
        + ax.get_yticklabels())
    for item in all_font_items:
        item.set_fontproperties(font_prop["Main"])

    ##########
    ## Plot ##
    ##########
    filename_Case = []
    plt_Case = []
    for i, case in enumerate(Case):
        def safe_load(key, default = None):
            preset = case.get("preset", "Default")
            return (case.get(key) or 
                    Preset[preset].get(key) or 
                    default)

        # Import case data
        path     = safe_load("path")
        filename = safe_load("filename")
        delimiter= safe_load("delimiter")
        nheader  = safe_load("nheader", 0)
        comment  = safe_load("comment", '#')
        datafile = path + "/" + filename

        try:
            data = np.genfromtxt(datafile, 
                                 delimiter=delimiter, 
                                 comments=comment, 
                                 skip_header=nheader)
        except IOError:
            print("%s file does not exists." % datafile)
            continue
        filename_Case.append(datafile)

        # Read case settings
        xcol    = safe_load("xcolumn")
        ycol    = safe_load("ycolumn")
        xmodify = str(safe_load("xmodify", "x"))
        ymodify = str(safe_load("ymodify", "y"))
        ls      = safe_load("linestyle", "-")
        lw      = safe_load("linewidth", 2.5)
        alpha   = safe_load("alpha", 1)
        c       = safe_load("color", __colorTable[i%__nColorTable])
        label   = safe_load("label", i)
        ls      = safe_load("linestyle", "-")
        lw      = safe_load("linewidth", 2.5)
        marker  = safe_load("marker")
        stride  = safe_load("stride", 1)
        xcol = np.array(xcol)
        ycol = np.array(ycol)
        # Allow picking color from colorTable by number
        try:
            c = __colorTable[(int(c)-1)%__nColorTable]
        except:
            pass

        # Modify values
        x = eval("(lambda x: " + xmodify + ")(data[:,xcol - 1])")
        y = eval("(lambda y: " + ymodify + ")(data[:,ycol - 1])")
        # Plot case data
        plt_Case.extend(
            plt.plot(x, y, 
                     c=c, alpha=alpha, lw=lw, ls=ls, 
                     label=label, marker=marker, markevery=stride))

    #############
    ## Scatter ##
    #############
    if Scatter is not None:
        for i, case in enumerate(Scatter):
            def safe_load(key, default = None):
                preset = case.get("preset", "Default")
                return (case.get(key) or 
                        Preset[preset].get(key) or 
                        default)
            # Import scatter data
            path     = safe_load("path")
            filename = safe_load("filename")
            delimiter= safe_load("delimiter")
            nheader  = safe_load("nheader", 0)
            comment  = safe_load("comment", '#')
            datafile = path + "/" + filename

            try:
                data = np.genfromtxt(datafile, delimiter=delimiter, comments=comment, skip_header=nheader)
            except IOError:
                print("%s file does not exists." % datafile)
                continue

            # Read scatter settings
            xcol    = safe_load("xcolumn")
            ycol    = safe_load("ycolumn")
            xmodify = str(safe_load("xmodify", "x"))
            ymodify = str(safe_load("ymodify", "y"))
            s       = safe_load("size")
            c       = safe_load("color", __colorTable[i%__nColorTable])
            marker  = safe_load("marker")
            alpha   = safe_load("alpha", 1)
            lw      = safe_load("edgewidths")
            edgec   = safe_load("edgecolors")
            xcol = np.array(xcol)
            ycol = np.array(ycol)
            # Allow picking color from colorTable by number
            try:
                c = __colorTable[(int(c)-1)%__nColorTable]
            except:
                pass

            # Plot case data
            x = eval("(lambda x: " + xmodify + ")(data[:,xcol - 1])")
            y = eval("(lambda y: " + ymodify + ")(data[:,ycol - 1])")
            plt.scatter(x, y, s=s, c=c, marker=marker, alpha=alpha, lw=lw, edgecolors=edgec)

    ############
    ## Legend ##
    ############
    if Legend is not None:
        legend_handle=plt_Case
        if (Legend.get("Custom") is not None and 
            Legend["useCustom"]):
            legend_handle = []
            for i, item in enumerate(Legend["Custom"]):
                def safe_load(key, default = None):
                    return item.get(key) or Default.get(key) or default
                # Read legend settings
                c       = safe_load("color", __colorTable[i%__nColorTable])
                label   = safe_load("label")
                lw      = safe_load("linewidth", 2.5)
                ls      = safe_load("linestyle", "-")
                marker  = safe_load("marker")
                ms      = safe_load("markersize", 10)
                alpha   = safe_load("alpha", 1)
                try:
                    c = __colorTable[(int(c)-1)%__nColorTable]
                except:
                    pass

                legend_handle.append(mpl.lines.Line2D(
                    [], [], alpha=alpha, c=c, label=label,
                    lw=lw, ls=ls, marker=marker, ms=ms))

        plt.legend(handles=legend_handle,
                   loc=Legend.get("location"),
                   prop=font_prop.get("Legend") or font_prop["Main"])

    ##########
    ## Text ##
    ##########
    if Text is not None:
        for text in Text:
            def safe_load(key, default = None):
                return text.get(key) or default
            x    = safe_load("x", 0)
            y    = safe_load("y", 0)
            body = safe_load("body", "")
            ha   = safe_load("horizontal alignment", "left")
            va   = safe_load("vertical alignment", "bottom")
            color= safe_load("color", "black")
            alpha= safe_load("alpha")
            plt.text(x, y, body, ha=ha, va=va, color=color, alpha=alpha,
                     fontproperties=(text.get("Font") or 
                                     font_prop.get("Text") or 
                                     font_prop["Main"]))
    #################
    ## Postprocess ##
    #################
    # Set Axes
    xlim_data = ax.get_xlim()
    ylim_data = ax.get_ylim()

    Figure.get("xstart",  xlim_data[0])
    Figure.get("xend",    xlim_data[1])
    Figure.get("xtick",  (xlim_data[1] - xlim_data[0]) // 5)
    Figure.get("ystart",  ylim_data[0])
    Figure.get("yend",    ylim_data[1])
    Figure.get("ytick",  (ylim_data[1] - ylim_data[0]) // 5)

    xrotation = Figure.get("xrotation")
    yrotation = Figure.get("yrotation")

    xticks=np.arange(Figure["xstart"],
                     Figure["xend"]+Figure["xtick"]//2,
                     Figure["xtick"])
    if Figure.get("xticks") is not None: xticks=Figure["xticks"]
    plt.xlabel(Figure["xlabel"])
    plt.xlim(Figure["xstart"], Figure["xend"])
    (
    plt.xticks(xticks, Figure["xlist"], rotation=xrotation) 
        if Figure.get("xlist") is not None 
        else plt.xticks(xticks, rotation=xrotation)
    )

    yticks=np.arange(Figure["ystart"],
                     Figure["yend"]+Figure["ytick"]//2,
                     Figure["ytick"])
    if Figure.get("yticks") is not None: yticks=Figure["yticks"]
    plt.ylabel(Figure["ylabel"])
    plt.ylim(Figure["ystart"], Figure["yend"])
    (
    plt.yticks(yticks, Figure["ylist"], rotation=yrotation)
        if Figure.get("ylist") is not None 
        else plt.yticks(yticks, rotation=yrotation)
    )

    # Draw grid lines
    for x in xticks:
        plt.plot((x, x),
                 (Figure["ystart"], Figure["yend"]),
                 "--",
                 lw=0.5,
                 color="black",
                 alpha=0.3)
    for y in yticks:
        plt.plot((Figure["xstart"], Figure["xend"]),
                 (y, y),
                 linestyle="--",
                 linewidth=0.5,
                 color="black",
                 alpha=0.3)

    ###################
    ## Export result ##
    ###################
    fig.tight_layout()
    plt.savefig("%s/%s" % (conf["savedir"], conf["savefilename"]),
                transparent = bool(Figure.get("transparent")))

    return filename_Case

########
# Main #
########
def __update(d, u):
    """
    Deep merge or update of a dictionary.
    """
    for key, value in u.items():
        if type(value) is dict:
            r = __update(d.get(key, {}), value)
            d[key] = r
        elif type(d) is dict and d.get(key) is None:
            d[key] = u[key]
        elif type(d) is dict and d is not None:
            pass
        else:
            d = {key: u[key]}
    return d

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Plot using matplotlib.")
    parser.add_argument(
        "yaml_setting_file",
        default="plot_settings.yml",
        help="specify a YAML plot-setting file")
    parser.add_argument(
        "-s", "--silent",
        help="suppress graph rendering",
        action="store_true")
    args = parser.parse_args()

    # Read .yml default / specific setting file
    try:
        script_path = os.path.split(os.path.realpath(__file__))[0]
        conf_default = yaml.safe_load(open(script_path+"/default_settings.yml"))
    except NameError:
        sys.exit("Run script standalone.")
    except IOError:
        sys.exit("Default setting file does not exist")
    try:
        conf = yaml.safe_load(open(args.yaml_setting_file))
        conf = __update(conf, conf_default)
    except IOError:
        sys.exit("Setting file %s does not exist" % args.yaml_setting_file)

    conf["savefilename"] = (conf.get("savefilename") or 
                            os.path.split(args.yaml_setting_file)[1])
    conf["savefilename"] = re.sub(r"(\..*)?$", ".png", conf["savefilename"])

    Case = makePlot(conf)
    print("Case:", "\n       ".join(Case))
    print("Output: %s" % conf["savefilename"])
    if not args.silent:
        subprocess.Popen(
            ["eog", "%s/%s" % (conf["savedir"], conf["savefilename"]), "&"])
