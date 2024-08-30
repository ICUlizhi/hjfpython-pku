from . import PeriodN


__all__ = ['ParabolicSAR', 'PSAR']


class _SarStatus(object):
    sar = None
    tr = None
    af = 0.0
    ep = 0.0

    def __str__(self):
        txt = []
        txt.append('sar: {}'.format(self.sar))
        txt.append('tr: {}'.format(self.tr))
        txt.append('af: {}'.format(self.af))
        txt.append('ep: {}'.format(self.ep))
        return '\n'.join(txt)


class ParabolicSAR(PeriodN):
    '''
    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"* for the RSI

    SAR stands for *Stop and Reverse* and the indicator was meant as a signal
    for entry (and reverse)

    How to select the 1st signal is left unspecified in the book and the
    increase/decrease of bars

    See:
      - https://en.wikipedia.org/wiki/Parabolic_SAR
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:parabolic_sar
    '''
    alias = ('PSAR',)
    lines = ('psar',)
    params = (
        ('period', 2),  
        ('af', 0.02),
        ('afmax', 0.20),
    )

    plotinfo = dict(subplot=False)
    plotlines = dict(
        psar=dict(
            marker='.', markersize=4.0, color='black', fillstyle='full', ls=''
        ),
    )

    def prenext(self):
        if len(self) == 1:
            self._status = []  
            return  

        elif len(self) == 2:
            self.nextstart()  
        else:
            self.next()  

        self.lines.psar[0] = float('NaN')  

    def nextstart(self):
        if self._status:  
            self.next()  
            return

        
        self._status = [_SarStatus(), _SarStatus()]

        
        
        
        
        
        
        plenidx = (len(self) - 1) % 2  
        status = self._status[plenidx]

        
        status.sar = (self.data.high[0] + self.data.low[0]) / 2.0

        status.af = self.p.af
        if self.data.close[0] >= self.data.close[-1]:  
            status.tr = not True  
            status.ep = self.data.low[-1]  
        else:
            status.tr = not False  
            status.ep = self.data.high[-1]  

        
        
        self.next()

    def next(self):
        hi = self.data.high[0]
        lo = self.data.low[0]

        plenidx = (len(self) - 1) % 2  
        status = self._status[plenidx]  

        tr = status.tr
        sar = status.sar

        
        if (tr and sar >= lo) or (not tr and sar <= hi):
            tr = not tr  
            sar = status.ep  
            ep = hi if tr else lo  
            af = self.p.af  

        else:  
            ep = status.ep
            af = status.af

        
        self.lines.psar[0] = sar

        
        if tr:  
            if hi > ep:
                ep = hi
                af = min(af + self.p.af, self.p.afmax)

        else:  
            if lo < ep:
                ep = lo
                af = min(af + self.p.af, self.p.afmax)

        sar = sar + af * (ep - sar)  

        
        if tr:  
            lo1 = self.data.low[-1]
            if sar > lo or sar > lo1:
                sar = min(lo, lo1)  
        else:
            hi1 = self.data.high[-1]
            if sar < hi or sar < hi1:
                sar = max(hi, hi1)  

        
        
        newstatus = self._status[not plenidx]
        newstatus.tr = tr
        newstatus.sar = sar
        newstatus.ep = ep
        newstatus.af = af
