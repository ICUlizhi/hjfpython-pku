from ..utils.py3 import range, zip

import matplotlib.collections as mcol
import matplotlib.colors as mcolors
import matplotlib.legend as mlegend
import matplotlib.lines as mlines

from .utils import shade_color


class CandlestickPlotHandler(object):
    legend_opens = [0.50, 0.50, 0.50]
    legend_highs = [1.00, 1.00, 1.00]
    legend_lows = [0.00, 0.00, 0.00]
    legend_closes = [0.80, 0.00, 1.00]

    def __init__(self,
                 ax, x, opens, highs, lows, closes,
                 colorup='k', colordown='r',
                 edgeup=None, edgedown=None,
                 tickup=None, tickdown=None,
                 width=1, tickwidth=1,
                 edgeadjust=0.05, edgeshading=-10,
                 alpha=1.0,
                 label='_nolegend',
                 fillup=True,
                 filldown=True,
                 **kwargs):

        
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha
        
        if edgeup:
            r, g, b = mcolors.colorConverter.to_rgb(edgeup)
            self.edgeup = ((r, g, b, alpha),)
        else:
            self.edgeup = shade_color(self.colorup, edgeshading)

        if edgedown:
            r, g, b = mcolors.colorConverter.to_rgb(edgedown)
            self.edgedown = ((r, g, b, alpha),)
        else:
            self.edgedown = shade_color(self.colordown, edgeshading)

            
        if tickup:
            r, g, b = mcolors.colorConverter.to_rgb(tickup)
            self.tickup = ((r, g, b, alpha),)
        else:
            self.tickup = self.edgeup

        if tickdown:
            r, g, b = mcolors.colorConverter.to_rgb(tickdown)
            self.tickdown = ((r, g, b, alpha),)
        else:
            self.tickdown = self.edgedown

        self.barcol, self.tickcol = self.barcollection(
            x, opens, highs, lows, closes,
            width, tickwidth, edgeadjust,
            label=label,
            fillup=fillup, filldown=filldown,
            **kwargs)

        
        ax.add_collection(self.tickcol)
        ax.add_collection(self.barcol)

        
        ax.update_datalim(((0, min(lows)), (len(opens), max(highs))))
        ax.autoscale_view()

        
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_opens)
        height = handlebox.height

        
        xs = [x0 + width * (i + 0.5) for i in range(len(self.legend_opens))]

        barcol, tickcol = self.barcollection(
            xs,
            self.legend_opens, self.legend_highs,
            self.legend_lows, self.legend_closes,
            width=width, tickwidth=2,
            scaling=height, bot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)
        tickcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(tickcol)

        return barcol, tickcol

    def barcollection(self,
                      xs,
                      opens, highs, lows, closes,
                      width, tickwidth=1, edgeadjust=0,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      fillup=True, filldown=True,
                      **kwargs):

        
        oc = lambda: zip(opens, closes)  
        xoc = lambda: zip(xs, opens, closes)  
        iohlc = lambda: zip(xs, opens, highs, lows, closes)  

        colorup = self.colorup if fillup else 'None'
        colordown = self.colordown if filldown else 'None'
        colord = {True: colorup, False: colordown}
        colors = [colord[o < c] for o, c in oc()]

        edgecolord = {True: self.edgeup, False: self.edgedown}
        edgecolors = [edgecolord[o < c] for o, c in oc()]

        tickcolord = {True: self.tickup, False: self.tickdown}
        tickcolors = [tickcolord[o < c] for o, c in oc()]

        delta = width / 2 - edgeadjust

        def barbox(i, open, close):
            
            left, right = i - delta, i + delta
            open = open * scaling + bot
            close = close * scaling + bot
            return (left, open), (left, close), (right, close), (right, open)

        barareas = [barbox(i, o, c) for i, o, c in xoc()]

        def tup(i, open, high, close):
            high = high * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, high), (i, max(open, close))

        tickrangesup = [tup(i, o, h, c) for i, o, h, l, c in iohlc()]

        def tdown(i, open, low, close):
            low = low * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, low), (i, min(open, close))

        tickrangesdown = [tdown(i, o, l, c) for i, o, h, l, c in iohlc()]

        
        useaa = 0,  
        lw = 0.5,   
        tlw = tickwidth,

        
        barcol = mcol.PolyCollection(
            barareas,
            facecolors=colors,
            edgecolors=edgecolors,
            antialiaseds=useaa,
            linewidths=lw,
            label=label,
            **kwargs)

        
        
        
        kwargs['zorder'] = barcol.get_zorder() * 0.9999

        
        tickcol = mcol.LineCollection(
            tickrangesup + tickrangesdown,
            colors=tickcolors,
            linewidths=tlw,
            antialiaseds=useaa,
            **kwargs)

        
        return barcol, tickcol


def plot_candlestick(ax,
                     x, opens, highs, lows, closes,
                     colorup='k', colordown='r',
                     edgeup=None, edgedown=None,
                     tickup=None, tickdown=None,
                     width=1, tickwidth=1.25,
                     edgeadjust=0.05, edgeshading=-10,
                     alpha=1.0,
                     label='_nolegend',
                     fillup=True,
                     filldown=True,
                     **kwargs):

    chandler = CandlestickPlotHandler(
        ax, x, opens, highs, lows, closes,
        colorup, colordown,
        edgeup, edgedown,
        tickup, tickdown,
        width, tickwidth,
        edgeadjust, edgeshading,
        alpha,
        label,
        fillup,
        filldown,
        **kwargs)

    
    
    return chandler.barcol, chandler.tickcol


class VolumePlotHandler(object):
    legend_vols = [0.5, 1.0, 0.75]
    legend_opens = [0, 1, 0]
    legend_closes = [1, 0, 1]

    def __init__(self,
                 ax, x, opens, closes, volumes,
                 colorup='k', colordown='r',
                 edgeup=None, edgedown=None,
                 edgeshading=-5, edgeadjust=0.05,
                 width=1, alpha=1.0,
                 **kwargs):

        
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha

        
        if not edgeup:
            self.edgeup = shade_color(self.colorup, edgeshading)
        else:
            r, g, b = mcolors.colorConverter.to_rgb(edgeup)
            self.edgeup = r, g, b, alpha

        if not edgedown:
            self.edgedown = shade_color(self.colordown, edgeshading)
        else:
            r, g, b = mcolors.colorConverter.to_rgb(edgedown)
            self.edgedown = r, g, b, alpha

        corners = (0, 0), (len(closes), max(volumes))
        ax.update_datalim(corners)
        ax.autoscale_view()

        self.barcol = self.barcollection(
            x, opens, closes, volumes,
            width=width, edgeadjust=edgeadjust,
            **kwargs)

        
        ax.add_collection(self.barcol)

        
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_vols)
        height = handlebox.height

        
        xs = [x0 + width * (i + 0.5) for i in range(len(self.legend_vols))]

        barcol = self.barcollection(
            xs, self.legend_opens, self.legend_closes, self.legend_vols,
            width=width, vscaling=height, vbot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)

        return barcol

    def barcollection(self,
                      x, opens, closes, vols,
                      width, edgeadjust=0,
                      vscaling=1.0, vbot=0,
                      **kwargs):

        
        openclose = lambda: zip(opens, closes)  

        
        colord = {True: self.colorup, False: self.colordown}
        colors = [colord[open < close] for open, close in openclose()]
        edgecolord = {True: self.edgeup, False: self.edgedown}
        edgecolors = [edgecolord[open < close] for open, close in openclose()]

        
        delta = width / 2 - edgeadjust

        
        def volbar(i, v):
            left, right = i - delta, i + delta
            v = vbot + v * vscaling
            return (left, vbot), (left, v), (right, v), (right, vbot)

        barareas = [volbar(i, v) for i, v in zip(x, vols)]
        barcol = mcol.PolyCollection(
            barareas,
            facecolors=colors,
            edgecolors=edgecolors,
            antialiaseds=(0,),
            linewidths=(0.5,),
            **kwargs)

        return barcol


def plot_volume(
        ax, x, opens, closes, volumes,
        colorup='k', colordown='r',
        edgeup=None, edgedown=None,
        edgeshading=-5, edgeadjust=0.05,
        width=1, alpha=1.0,
        **kwargs):

    vhandler = VolumePlotHandler(
        ax, x, opens, closes, volumes,
        colorup, colordown,
        edgeup, edgedown,
        edgeshading, edgeadjust,
        width, alpha,
        **kwargs)

    return vhandler.barcol,


class OHLCPlotHandler(object):
    legend_opens = [0.50, 0.50, 0.50]
    legend_highs = [1.00, 1.00, 1.00]
    legend_lows = [0.00, 0.00, 0.00]
    legend_closes = [0.80, 0.20, 0.90]

    def __init__(self,
                 ax, x, opens, highs, lows, closes,
                 colorup='k', colordown='r',
                 width=1, tickwidth=0.5,
                 alpha=1.0,
                 label='_nolegend',
                 **kwargs):

        
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha

        bcol, ocol, ccol = self.barcollection(
            x, opens, highs, lows, closes,
            width=width, tickwidth=tickwidth,
            label=label,
            **kwargs)

        self.barcol = bcol
        self.opencol = ocol
        self.closecol = ccol

        
        ax.add_collection(self.barcol)
        ax.add_collection(self.opencol)
        ax.add_collection(self.closecol)

        
        ax.update_datalim(((0, min(lows)), (len(opens), max(highs))))
        ax.autoscale_view()

        
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_opens)
        height = handlebox.height

        
        xs = [x0 + width * (i + 0.5) for i in range(len(self.legend_opens))]

        barcol, opencol, closecol = self.barcollection(
            xs,
            self.legend_opens, self.legend_highs,
            self.legend_lows, self.legend_closes,
            width=1.5, tickwidth=2,
            scaling=height, bot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)
        
        handlebox.add_artist(opencol)
        
        handlebox.add_artist(closecol)

        return barcol, opencol, closecol

    def barcollection(self,
                      xs,
                      opens, highs, lows, closes,
                      width, tickwidth,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      **kwargs):

        
        ihighlow = lambda: zip(xs, highs, lows)  
        iopen = lambda: zip(xs, opens)  
        iclose = lambda: zip(xs, closes)  
        openclose = lambda: zip(opens, closes)  

        colord = {True: self.colorup, False: self.colordown}
        colors = [colord[open < close] for open, close in openclose()]

        
        useaa = 0,
        lw = width,
        tlw = tickwidth,

        
        def barrange(i, high, low):
            return (i, low * scaling + bot), (i, high * scaling + bot)

        barranges = [barrange(i, high, low) for i, high, low in ihighlow()]

        barcol = mcol.LineCollection(
            barranges,
            colors=colors,
            linewidths=lw,
            antialiaseds=useaa,
            label=label,
            **kwargs)

        def tickopen(i, open):
            open = open * scaling + bot
            return (i - tickwidth, open), (i, open)

        openticks = [tickopen(i, open) for i, open in iopen()]
        opencol = mcol.LineCollection(
            openticks,
            colors=colors,
            antialiaseds=useaa,
            linewidths=tlw,
            label='_nolegend',
            **kwargs)

        def tickclose(i, close):
            close = close * scaling + bot
            return (i, close), (i + tickwidth, close)

        closeticks = [tickclose(i, close) for i, close in iclose()]
        closecol = mcol.LineCollection(
            closeticks,
            colors=colors,
            antialiaseds=useaa,
            linewidths=tlw,
            label='_nolegend',
            **kwargs)

        
        return barcol, opencol, closecol


def plot_ohlc(ax, x, opens, highs, lows, closes,
              colorup='k', colordown='r',
              width=1.5, tickwidth=0.5,
              alpha=1.0,
              label='_nolegend',
              **kwargs):

    handler = OHLCPlotHandler(
        ax, x, opens, highs, lows, closes,
        colorup, colordown,
        width, tickwidth,
        alpha,
        label,
        **kwargs)

    return handler.barcol, handler.opencol, handler.closecol


class LineOnClosePlotHandler(object):
    legend_closes = [0.00, 0.66, 0.33, 1.00]

    def __init__(self,
                 ax, x, closes, color='k',
                 width=1, alpha=1.0,
                 label='_nolegend',
                 **kwargs):

        self.color = color
        self.alpha = alpha

        self.loc, = self.barcollection(
            x, closes,
            width=width,
            label=label,
            **kwargs)

        
        ax.add_line(self.loc)

        
        ax.update_datalim(((x[0], min(closes)), (x[-1], max(closes))))
        ax.autoscale_view()

        
        mlegend.Legend.update_default_handler_map({self.loc: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0 = handlebox.xdescent
        y0 = handlebox.ydescent
        width = handlebox.width / len(self.legend_closes)
        height = handlebox.height

        
        xs = [x0 + width * (i + 0.5) for i in range(len(self.legend_closes))]

        linecol, = self.barcollection(
            xs, self.legend_closes,
            width=1.5,
            scaling=height, bot=y0)

        linecol.set_transform(handlebox.get_transform())
        handlebox.add_artist(linecol)

        return linecol,

    def barcollection(self,
                      xs, closes,
                      width,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      **kwargs):

        
        scaled = [close * scaling + bot for close in closes]

        loc = mlines.Line2D(
            xs, scaled,
            color=self.color,
            lw=width,
            label=label,
            alpha=self.alpha,
            **kwargs)

        return loc,


def plot_lineonclose(ax, x, closes,
                     color='k',
                     width=1.5,
                     alpha=1.0,
                     label='_nolegend',
                     **kwargs):

    handler = LineOnClosePlotHandler(
        ax, x, closes,
        color=color, width=width,
        alpha=alpha, label=label,
        **kwargs)

    return handler.loc,
