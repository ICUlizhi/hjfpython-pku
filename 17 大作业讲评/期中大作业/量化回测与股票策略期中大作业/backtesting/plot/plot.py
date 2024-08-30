import bisect
import collections
import datetime
import itertools
import math
import operator
import sys

import matplotlib
import numpy as np  
import matplotlib.dates as mdates
import matplotlib.font_manager as mfontmgr
import matplotlib.legend as mlegend
import matplotlib.ticker as mticker

from ..utils.py3 import range, with_metaclass, string_types, integer_types
from .. import AutoInfoClass, MetaParams, TimeFrame, date2num

from .finance import plot_candlestick, plot_ohlc, plot_volume, plot_lineonclose
from .formatters import (MyVolFormatter, MyDateFormatter, getlocator)
from . import locator as loc
from .multicursor import MultiCursor
from .scheme import PlotScheme
from .utils import tag_box_style


class PInfo(object):
    def __init__(self, sch):
        self.sch = sch
        self.nrows = 0
        self.row = 0
        self.clock = None
        self.x = None
        self.xlen = 0
        self.sharex = None
        self.figs = list()
        self.cursors = list()
        self.daxis = collections.OrderedDict()
        self.vaxis = list()
        self.zorder = dict()
        self.coloridx = collections.defaultdict(lambda: -1)
        self.handles = collections.defaultdict(list)
        self.labels = collections.defaultdict(list)
        self.legpos = collections.defaultdict(int)

        self.prop = mfontmgr.FontProperties(size=self.sch.subtxtsize)

    def newfig(self, figid, numfig, mpyplot):
        fig = mpyplot.figure(figid + numfig)
        self.figs.append(fig)
        self.daxis = collections.OrderedDict()
        self.vaxis = list()
        self.row = 0
        self.sharex = None
        return fig

    def nextcolor(self, ax):
        self.coloridx[ax] += 1
        return self.coloridx[ax]

    def color(self, ax):
        return self.sch.color(self.coloridx[ax])

    def zordernext(self, ax):
        z = self.zorder[ax]
        if self.sch.zdown:
            return z * 0.9999
        return z * 1.0001

    def zordercur(self, ax):
        return self.zorder[ax]


class Plot_OldSync(with_metaclass(MetaParams, object)):
    params = (('scheme', PlotScheme()),)

    def __init__(self, **kwargs):
        for pname, pvalue in kwargs.items():
            setattr(self.p.scheme, pname, pvalue)
        if not hasattr(self.p.scheme, 'locbg'):
            setattr(self.p.scheme, 'locbg', 'white')
            setattr(self.p.scheme, 'locbgother', 'white')

    def drawtag(self, ax, x, y, facecolor, edgecolor, alpha=0.9, **kwargs):

        txt = ax.text(x, y, '%.2f' % y, va='center', ha='left',
                      fontsize=self.pinf.sch.subtxtsize,
                      bbox=dict(boxstyle=tag_box_style,
                                facecolor=facecolor,
                                edgecolor=edgecolor,
                                alpha=alpha),
                      
                      zorder=self.pinf.zorder[ax] + 3.0,
                      **kwargs)

    def plot(self, strategy, figid=0, numfigs=1, iplot=True,
             start=None, end=None, **kwargs):
        
        if not strategy.datas:
            return

        if not len(strategy):
            return

        if iplot:
            if 'ipykernel' in sys.modules:
                matplotlib.use('nbagg')

        
        import matplotlib.pyplot as mpyplot
        self.mpyplot = mpyplot

        self.pinf = PInfo(self.p.scheme)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  

        slen = len(st_dtime[start:end])
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i + start
            if i == (numfigs - 1):
                d += m  
            b = a + d

            pranges.append([a, b, d])

        figs = []

        for numfig in range(numfigs):
            
            fig = self.pinf.newfig(figid, numfig, self.mpyplot)
            figs.append(fig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy
            self.pinf.xreal = self.pinf.clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))
            
            
            
            
            

            
            
            self.pinf.xdata = self.pinf.x
            for ptop in self.dplotstop:
                self.plotind(None, ptop, subinds=self.dplotsover[ptop])

            
            dt0, dt1 = self.pinf.xreal[0], self.pinf.xreal[-1]
            for data in strategy.datas:
                if not data.plotinfo.plot:
                    continue

                self.pinf.xdata = self.pinf.x
                xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
                if len(xd) < self.pinf.xlen:
                    self.pinf.xdata = xdata = []
                    xreal = self.pinf.xreal
                    dts = data.datetime.plot()
                    xtemp = list()
                    for dt in (x for x in dts if dt0 <= x <= dt1):
                        dtidx = bisect.bisect_left(xreal, dt)
                        xdata.append(dtidx)
                        xtemp.append(dt)

                    self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                    self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])

                for ind in self.dplotsup[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsdown[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            laxis = list(self.pinf.daxis.values())

            
            i = -1
            while True:
                lastax = laxis[i]
                if lastax not in self.pinf.vaxis:
                    break

                i -= 1

            self.setlocators(lastax)  

            
            
            
            
            for ax in laxis:
                self.mpyplot.setp(ax.get_xticklabels(), visible=False)

            self.mpyplot.setp(lastax.get_xticklabels(), visible=True,
                              rotation=self.pinf.sch.tickrotation)

            
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            self.mpyplot.autoscale(enable=True, axis=axtight, tight=True)

        return figs

    def setlocators(self, ax):
        clock = sorted(self.pinf.clock.datas,
                       key=lambda x: (x._timeframe, x._compression))[0]

        comp = getattr(clock, '_compression', 1)
        tframe = getattr(clock, '_timeframe', TimeFrame.Days)

        if self.pinf.sch.fmt_x_data is None:
            if tframe == TimeFrame.Years:
                fmtdata = '%Y'
            elif tframe == TimeFrame.Months:
                fmtdata = '%Y-%m'
            elif tframe == TimeFrame.Weeks:
                fmtdata = '%Y-%m-%d'
            elif tframe == TimeFrame.Days:
                fmtdata = '%Y-%m-%d'
            elif tframe == TimeFrame.Minutes:
                fmtdata = '%Y-%m-%d %H:%M'
            elif tframe == TimeFrame.Seconds:
                fmtdata = '%Y-%m-%d %H:%M:%S'
            elif tframe == TimeFrame.MicroSeconds:
                fmtdata = '%Y-%m-%d %H:%M:%S.%f'
            elif tframe == TimeFrame.Ticks:
                fmtdata = '%Y-%m-%d %H:%M:%S.%f'
        else:
            fmtdata = self.pinf.sch.fmt_x_data

        fordata = MyDateFormatter(self.pinf.xreal, fmt=fmtdata)
        for dax in self.pinf.daxis.values():
            dax.fmt_xdata = fordata

        
        locmajor = loc.AutoDateLocator(self.pinf.xreal)
        ax.xaxis.set_major_locator(locmajor)
        if self.pinf.sch.fmt_x_ticks is None:
            autofmt = loc.AutoDateFormatter(self.pinf.xreal, locmajor)
        else:
            autofmt = MyDateFormatter(self.pinf.xreal,
                                      fmt=self.pinf.sch.fmt_x_ticks)
        ax.xaxis.set_major_formatter(autofmt)

    def calcrows(self, strategy):
        
        rowsmajor = self.pinf.sch.rowsmajor
        rowsminor = self.pinf.sch.rowsminor
        nrows = 0

        datasnoplot = 0
        for data in strategy.datas:
            if not data.plotinfo.plot:
                
                datasnoplot += 1
                self.dplotsup.pop(data, None)
                self.dplotsdown.pop(data, None)
                self.dplotsover.pop(data, None)

            else:
                pmaster = data.plotinfo.plotmaster
                if pmaster is data:
                    pmaster = None
                if pmaster is not None:
                    
                    if self.pinf.sch.volume:
                        nrows += rowsminor
                else:
                    
                    nrows += rowsmajor
                    if self.pinf.sch.volume and not self.pinf.sch.voloverlay:
                        nrows += rowsminor

        if False:
            
            nrows += (len(strategy.datas) - datasnoplot) * rowsmajor
            if self.pinf.sch.volume and not self.pinf.sch.voloverlay:
                nrows += (len(strategy.datas) - datasnoplot) * rowsminor

        
        nrows += len(self.dplotstop) * rowsminor

        
        nrows += sum(len(v) for v in self.dplotsup.values())
        nrows += sum(len(v) for v in self.dplotsdown.values())

        self.pinf.nrows = nrows

    def newaxis(self, obj, rowspan):
        ax = self.mpyplot.subplot2grid(
            (self.pinf.nrows, 1), (self.pinf.row, 0),
            rowspan=rowspan, sharex=self.pinf.sharex)

        
        if self.pinf.sharex is None:
            self.pinf.sharex = ax

        
        self.pinf.row += rowspan

        
        self.pinf.daxis[obj] = ax

        
        ax.yaxis.tick_right()
        ax.grid(self.pinf.sch.grid, which='both')

        return ax

    def plotind(self, iref, ind,
                subinds=None, upinds=None, downinds=None,
                masterax=None):

        sch = self.p.scheme

        
        subinds = subinds or []
        upinds = upinds or []
        downinds = downinds or []

        
        for upind in upinds:
            self.plotind(iref, upind)

        
        ax = masterax or self.newaxis(ind, rowspan=self.pinf.sch.rowsminor)

        indlabel = ind.plotlabel()

        
        
        toskip = 0
        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)
            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)
            if not lineplotinfo:
                lineplotinfo = AutoInfoClass()
            pltmethod = lineplotinfo._get('_method', 'plot')
            if pltmethod != 'plot':
                toskip += 1 - lineplotinfo._get('_plotskip', False)

        if toskip >= ind.size():
            toskip = 0

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)

            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)

            if not lineplotinfo:
                lineplotinfo = AutoInfoClass()

            if lineplotinfo._get('_plotskip', False):
                continue

            
            if masterax and not ind.plotinfo.plotlinelabels:
                label = indlabel * (not toskip) or '_nolegend'
            else:
                label = (indlabel + '\n') * (not toskip)
                label += lineplotinfo._get('_name', '') or linealias

            toskip -= 1  

            
            lplot = line.plotrange(self.pinf.xstart, self.pinf.xend)

            
            if self.pinf.sch.linevalues and ind.plotinfo.plotlinevalues:
                plotlinevalue = lineplotinfo._get('_plotvalue', True)
                if plotlinevalue and not math.isnan(lplot[-1]):
                    label += ' %.2f' % lplot[-1]

            plotkwargs = dict()
            linekwargs = lineplotinfo._getkwargs(skip_=True)

            if linekwargs.get('color', None) is None:
                if not lineplotinfo._get('_samecolor', False):
                    self.pinf.nextcolor(ax)
                plotkwargs['color'] = self.pinf.color(ax)

            plotkwargs.update(dict(aa=True, label=label))
            plotkwargs.update(**linekwargs)

            if ax in self.pinf.zorder:
                plotkwargs['zorder'] = self.pinf.zordernext(ax)

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))

            xdata, lplotarray = self.pinf.xdata, lplot
            if lineplotinfo._get('_skipnan', False):
                
                lplotarray = np.array(lplot)
                lplotmask = np.isfinite(lplotarray)

                
                lplotarray = lplotarray[lplotmask]
                xdata = np.array(xdata)[lplotmask]

            plottedline = pltmethod(xdata, lplotarray, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                
                pass

            self.pinf.zorder[ax] = plottedline.get_zorder()

            vtags = lineplotinfo._get('plotvaluetags', True)
            if self.pinf.sch.valuetags and vtags:
                linetag = lineplotinfo._get('_plotvaluetag', True)
                if linetag and not math.isnan(lplot[-1]):
                    
                    self.drawtag(ax, len(self.pinf.xreal), lplot[-1],
                                 facecolor=self.pinf.sch.locbgother,
                                 edgecolor=self.pinf.color(ax))

            farts = (('_gt', operator.gt), ('_lt', operator.lt), ('', None),)
            for fcmp, fop in farts:
                fattr = '_fill' + fcmp
                fref, fcol = lineplotinfo._get(fattr, (None, None))
                if fref is not None:
                    y1 = np.array(lplot)
                    if isinstance(fref, integer_types):
                        y2 = np.full_like(y1, fref)
                    else:  
                        l2 = getattr(ind, fref)
                        prl2 = l2.plotrange(self.pinf.xstart, self.pinf.xend)
                        y2 = np.array(prl2)
                    kwargs = dict()
                    if fop is not None:
                        kwargs['where'] = fop(y1, y2)

                    falpha = self.pinf.sch.fillalpha
                    if isinstance(fcol, (list, tuple)):
                        fcol, falpha = fcol

                    ax.fill_between(self.pinf.xdata, y1, y2,
                                    facecolor=fcol,
                                    alpha=falpha,
                                    interpolate=True,
                                    **kwargs)

        
        for subind in subinds:
            self.plotind(iref, subind, subinds=self.dplotsover[subind],
                         masterax=ax)

        if not masterax:
            
            ymargin = ind.plotinfo._get('plotymargin', 0.0)
            ymargin = max(ymargin, self.pinf.sch.yadjust)
            if ymargin:
                ax.margins(y=ymargin)

            
            yticks = ind.plotinfo._get('plotyticks', [])
            if not yticks:
                yticks = ind.plotinfo._get('plotyhlines', [])

            if yticks:
                ax.set_yticks(yticks)
            else:
                locator = mticker.MaxNLocator(nbins=4, prune='both')
                ax.yaxis.set_major_locator(locator)

            
            hlines = ind.plotinfo._get('plothlines', [])
            if not hlines:
                hlines = ind.plotinfo._get('plotyhlines', [])
            for hline in hlines:
                ax.axhline(hline, color=self.pinf.sch.hlinescolor,
                           ls=self.pinf.sch.hlinesstyle,
                           lw=self.pinf.sch.hlineswidth)

            if self.pinf.sch.legendind and \
               ind.plotinfo._get('plotlegend', True):

                handles, labels = ax.get_legend_handles_labels()
                
                if labels:
                    
                    loc = ind.plotinfo.legendloc or self.pinf.sch.legendindloc

                    
                    legend = ax.legend(loc=loc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

                    
                    
                    
                    legend._legend_box.align = 'left'

        
        for downind in downinds:
            self.plotind(iref, downind)

    def plotvolume(self, data, opens, highs, lows, closes, volumes, label):
        pmaster = data.plotinfo.plotmaster
        if pmaster is data:
            pmaster = None
        voloverlay = (self.pinf.sch.voloverlay and pmaster is None)

        
        if voloverlay:
            rowspan = self.pinf.sch.rowsmajor
        else:
            rowspan = self.pinf.sch.rowsminor

        ax = self.newaxis(data.volume, rowspan=rowspan)

        
        if voloverlay:
            volalpha = self.pinf.sch.voltrans
        else:
            volalpha = 1.0

        maxvol = volylim = max(volumes)
        if maxvol:

            
            vollabel = label
            volplot, = plot_volume(ax, self.pinf.xdata, opens, closes, volumes,
                                   colorup=self.pinf.sch.volup,
                                   colordown=self.pinf.sch.voldown,
                                   alpha=volalpha, label=vollabel)

            nbins = 6
            prune = 'both'
            
            if voloverlay:
                
                nbins = int(nbins / self.pinf.sch.volscaling)
                prune = None

                volylim /= self.pinf.sch.volscaling
                ax.set_ylim(0, volylim, auto=True)
            else:
                
                handles, labels = ax.get_legend_handles_labels()
                if handles:

                    
                    loc = data.plotinfo.legendloc or self.pinf.sch.legendindloc

                    
                    legend = ax.legend(loc=loc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

            locator = mticker.MaxNLocator(nbins=nbins, prune=prune)
            ax.yaxis.set_major_locator(locator)
            ax.yaxis.set_major_formatter(MyVolFormatter(maxvol))

        if not maxvol:
            ax.set_yticks([])
            return None

        return volplot

    def plotdata(self, data, indicators):
        for ind in indicators:
            upinds = self.dplotsup[ind]
            for upind in upinds:
                self.plotind(data, upind,
                             subinds=self.dplotsover[upind],
                             upinds=self.dplotsup[upind],
                             downinds=self.dplotsdown[upind])

        opens = data.open.plotrange(self.pinf.xstart, self.pinf.xend)
        highs = data.high.plotrange(self.pinf.xstart, self.pinf.xend)
        lows = data.low.plotrange(self.pinf.xstart, self.pinf.xend)
        closes = data.close.plotrange(self.pinf.xstart, self.pinf.xend)
        volumes = data.volume.plotrange(self.pinf.xstart, self.pinf.xend)

        vollabel = 'Volume'
        pmaster = data.plotinfo.plotmaster
        if pmaster is data:
            pmaster = None

        datalabel = ''
        if hasattr(data, '_name') and data._name:
            datalabel += data._name

        voloverlay = (self.pinf.sch.voloverlay and pmaster is None)

        if not voloverlay:
            vollabel += ' ({})'.format(datalabel)

        
        axdatamaster = None
        if self.pinf.sch.volume and voloverlay:
            volplot = self.plotvolume(
                data, opens, highs, lows, closes, volumes, vollabel)
            axvol = self.pinf.daxis[data.volume]
            ax = axvol.twinx()
            self.pinf.daxis[data] = ax
            self.pinf.vaxis.append(ax)
        else:
            if pmaster is None:
                ax = self.newaxis(data, rowspan=self.pinf.sch.rowsmajor)
            elif getattr(data.plotinfo, 'sameaxis', False):
                axdatamaster = self.pinf.daxis[pmaster]
                ax = axdatamaster
            else:
                axdatamaster = self.pinf.daxis[pmaster]
                ax = axdatamaster.twinx()
                self.pinf.vaxis.append(ax)

        if hasattr(data, '_compression') and \
           hasattr(data, '_timeframe'):
            tfname = TimeFrame.getname(data._timeframe, data._compression)
            datalabel += ' (%d %s)' % (data._compression, tfname)

        plinevalues = getattr(data.plotinfo, 'plotlinevalues', True)
        if self.pinf.sch.style.startswith('line'):
            if self.pinf.sch.linevalues and plinevalues:
                datalabel += ' C:%.2f' % closes[-1]

            if axdatamaster is None:
                color = self.pinf.sch.loc
            else:
                self.pinf.nextcolor(axdatamaster)
                color = self.pinf.color(axdatamaster)

            plotted = plot_lineonclose(
                ax, self.pinf.xdata, closes,
                color=color, label=datalabel)
        else:
            if self.pinf.sch.linevalues and plinevalues:
                datalabel += ' O:%.2f H:%.2f L:%.2f C:%.2f' % \
                             (opens[-1], highs[-1], lows[-1], closes[-1])
            if self.pinf.sch.style.startswith('candle'):
                plotted = plot_candlestick(
                    ax, self.pinf.xdata, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel,
                    alpha=self.pinf.sch.baralpha,
                    fillup=self.pinf.sch.barupfill,
                    filldown=self.pinf.sch.bardownfill)

            elif self.pinf.sch.style.startswith('bar') or True:
                
                plotted = plot_ohlc(
                    ax, self.pinf.xdata, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

        self.pinf.zorder[ax] = plotted[0].get_zorder()

        
        vtags = data.plotinfo._get('plotvaluetags', True)
        if self.pinf.sch.valuetags and vtags:
            self.drawtag(ax, len(self.pinf.xreal), closes[-1],
                         facecolor=self.pinf.sch.locbg,
                         edgecolor=self.pinf.sch.loc)

        ax.yaxis.set_major_locator(mticker.MaxNLocator(prune='both'))
        
        if data.plotinfo._get('plotylimited', True):
            if axdatamaster is None:
                ax.set_ylim(ax.get_ylim())

        if self.pinf.sch.volume:
            
            if not voloverlay:
                self.plotvolume(
                    data, opens, highs, lows, closes, volumes, vollabel)
            else:
                
                if self.pinf.sch.volpushup:
                    
                    axbot, axtop = ax.get_ylim()
                    axbot *= (1.0 - self.pinf.sch.volpushup)
                    ax.set_ylim(axbot, axtop)

        for ind in indicators:
            self.plotind(data, ind, subinds=self.dplotsover[ind], masterax=ax)

        handles, labels = ax.get_legend_handles_labels()
        a = axdatamaster or ax
        if handles:
            
            
            
            

            ai = self.pinf.legpos[a]
            if self.pinf.sch.volume and voloverlay:
                if volplot:
                    
                    labels.insert(ai, vollabel)
                    handles.insert(ai, volplot)

            didx = labels.index(datalabel)
            labels.insert(ai, labels.pop(didx))
            handles.insert(ai, handles.pop(didx))

            if axdatamaster is None:
                self.pinf.handles[ax] = handles
                self.pinf.labels[ax] = labels
            else:
                self.pinf.handles[axdatamaster] = handles
                self.pinf.labels[axdatamaster] = labels
                
                

            h = self.pinf.handles[a]
            l = self.pinf.labels[a]

            axlegend = a
            loc = data.plotinfo.legendloc or self.pinf.sch.legenddataloc
            legend = axlegend.legend(h, l,
                                     loc=loc,
                                     frameon=False, shadow=False,
                                     fancybox=False, prop=self.pinf.prop,
                                     numpoints=1, ncol=1)

            
            
            legend._legend_box.align = 'left'

        for ind in indicators:
            downinds = self.dplotsdown[ind]
            for downind in downinds:
                self.plotind(data, downind,
                             subinds=self.dplotsover[downind],
                             upinds=self.dplotsup[downind],
                             downinds=self.dplotsdown[downind])

        self.pinf.legpos[a] = len(self.pinf.handles[a])

        if data.plotinfo._get('plotlog', False):
            a = axdatamaster or ax
            a.set_yscale('log')

    def show(self):
        self.mpyplot.show()

    def savefig(self, fig, filename, width=16, height=9, dpi=300, tight=True):
        fig.set_size_inches(width, height)
        bbox_inches = 'tight' * tight or None
        fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)

    def sortdataindicators(self, strategy):
        
        self.dplotstop = list()
        self.dplotsup = collections.defaultdict(list)
        self.dplotsdown = collections.defaultdict(list)
        self.dplotsover = collections.defaultdict(list)

        
        for x in strategy.getobservers():
            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            if x.plotinfo.subplot:
                self.dplotstop.append(x)
            else:
                key = getattr(x._clock, 'owner', x._clock)
                self.dplotsover[key].append(x)

        
        for x in strategy.getindicators():
            if not hasattr(x, 'plotinfo'):
                
                continue

            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            x._plotinit()  

            
            key = getattr(x._clock, 'owner', x._clock)
            if key is strategy:  
                key = strategy.data

            if getattr(x.plotinfo, 'plotforce', False):
                if key not in strategy.datas:
                    datas = strategy.datas
                    while True:
                        if key not in strategy.datas:
                            key = key._clock
                        else:
                            break

            xpmaster = x.plotinfo.plotmaster
            if xpmaster is x:
                xpmaster = None
            if xpmaster is not None:
                key = xpmaster

            if x.plotinfo.subplot and xpmaster is None:
                if x.plotinfo.plotabove:
                    self.dplotsup[key].append(x)
                else:
                    self.dplotsdown[key].append(x)
            else:
                self.dplotsover[key].append(x)


Plot = Plot_OldSync
