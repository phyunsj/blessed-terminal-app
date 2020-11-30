#!/usr/bin/env python
from __future__ import print_function

import sys
import time
import random
import requests
import lxml.html
#from bs4 import BeautifulSoup as bs
from blessed import Terminal
from colorama import Fore, Back, Style, Cursor
import yahoo_fin.stock_info as si
import pandas as pd

border_h = u"─"
border_v = u"│"
 
class StockTickerLine:
    def __init__(self, width, direction = 1, xPos = 0, yPos = 1,  col = 1, offset = 1, charSize = 6, tickerLen = 0 ):
        self.width = width
        self.direction = direction
        self.charSize = charSize # "6" chars to display one charactor
        self.tickerLen = tickerLen
        self.col = col
        self.offset = offset
        self.xPos = xPos
        self.yPos = yPos
        self.msg = ''
        self.screenCharSize  = self.width * self.charSize
        self.backward_counter = 1
        self.firstTickerSize = 0
    
    def setFirstTickerSize(self, charSize):
        self.firstTickerSize = charSize
        
    def append(self, msg):
        if self.direction > 0 :
            self.msg = msg + self.msg
        else:
            self.msg = self.msg + msg
        self.tickerLen += len(msg)

    def write(self, term):
        if self.direction > 0 :        
            return self.forward_write(term)
        else:
            return self.backward_write(term)

            
    def forward_write(self, term):
    
        sys.stderr.write(term.move_yx(self.yPos, self.xPos)) 
        
        msg_size = self.col*self.charSize

        if self.col <= self.width:
            if self.firstTickerSize <= 0:
                sys.stderr.write(self.msg[-msg_size:])
                sys.stderr.flush()

                self.col += self.offset
                if msg_size >= self.tickerLen:
                    return True, False
                else:
                    return False, False
            else:
                self.firstTickerSize -= self.charSize
                return False, False
        else: 
            self.msg = self.msg[:-self.charSize]           
            sys.stderr.write(self.msg[-self.screenCharSize:-1])
            sys.stderr.flush()
                
            self.tickerLen -= self.charSize
            if self.tickerLen <= self.screenCharSize:
                return True, True
            else:
                return False, True
                
    def backward_write(self, term):
    
        sys.stderr.write(term.move_yx(self.yPos, self.xPos - self.backward_counter))
        
        msg_size = self.backward_counter*self.charSize
        
        if self.col > 0:
            if self.firstTickerSize <= 0:
                sys.stderr.write(self.msg[:msg_size])
                sys.stderr.flush()

                self.backward_counter += 1
            
                self.col -= self.offset
                if msg_size >= self.tickerLen:
                    return True, False
                else:
                    return False, False
            else:
                self.firstTickerSize -= self.charSize
                return False, False
        else: 
            self.msg = self.msg[self.charSize:]           
            sys.stderr.write(self.msg[:self.screenCharSize])
            sys.stderr.flush()
                
            self.tickerLen -= self.charSize
            if self.tickerLen <= self.screenCharSize:
                return True, True
            else:
                return False, True
                
def printNumber( option, stockNumber ):
    return ''.join([ option+letter for letter in stockNumber ])

def printDateTime( term, yPos, xPos, elapsed_time ):
    sys.stderr.write(term.move_yx( yPos, xPos) + '   '+ Style.RESET_ALL + Style.BRIGHT + Back.BLUE + ' '+time.asctime( time.localtime(time.time()) ) + ' '+Style.RESET_ALL )
    #sys.stderr.write(term.move_yx( yPos, xPos) + '   '+ Style.RESET_ALL + Style.BRIGHT + Back.BLUE + ' '+time.asctime( time.localtime(time.time()) ) + ' ('+str(elapsed_time)+') '+Style.RESET_ALL )

def printLine( term, yPos, xPos, size ):
    sys.stderr.write(term.move_yx( yPos, xPos) + border_h * size )
 
def printMenu ( term ):
    sys.stderr.write(term.move_yx(term.height, 0) + "'X' to stop.")

def clearScreen ( term ):
    sys.stderr.write(term.home + term.clear)
    
def resetPosition ( term ):
    sys.stderr.write(term.move_yx(1, 0))
    
def printIndexTitle ( term, yPos, xPos, symbol ):
    sys.stderr.write(term.move_yx( yPos, xPos) + Style.RESET_ALL + Style.BRIGHT + Back.BLACK + symbol + Style.RESET_ALL )

def printDivider ( term, yPos, xPos, size ):
    for n in range(0, size, 1):
        sys.stderr.write(term.move_yx( yPos + n, xPos) + border_v )
    
def printIndexPrice( term, symbol, yPos, xPos ):
    stock = si.get_data(symbol, end_date = pd.Timestamp.today() + pd.DateOffset(10))[-2:] 
    live_price = round(stock.close[-1], 2)  # live data
    close_price = round(stock.close[-2], 2)  # previously closed price
    price = round(live_price - close_price, 2)
    percent = round( price * 100 / close_price, 2)
    if price > 0 :
        sys.stderr.write(term.move_yx( yPos, xPos) + Style.RESET_ALL + Fore.GREEN + f'{live_price:,.2f}   ' + Style.RESET_ALL )
        sys.stderr.write(term.move_yx( yPos+1, xPos) + Style.RESET_ALL + Fore.GREEN + f'{price:,.2f} ({percent:.2f}%)  ' + Style.RESET_ALL )        
    elif price == 0 :
        sys.stderr.write(term.move_yx( yPos, xPos) + Style.RESET_ALL + Fore.BLUE + f'{live_price:,.2f}   ' + Style.RESET_ALL ) 
        sys.stderr.write(term.move_yx( yPos+1, xPos) + Style.RESET_ALL + Fore.BLUE + f'{price:,} ({percent:.2f}%)  ' + Style.RESET_ALL )        
    else:
        sys.stderr.write(term.move_yx( yPos, xPos) + Style.RESET_ALL + Fore.RED + f'{live_price:,.2f}   ' + Style.RESET_ALL )
        sys.stderr.write(term.move_yx( yPos+1, xPos) + Style.RESET_ALL + Fore.RED + f'{price:,.2f} ({percent:.2f}%)  ' + Style.RESET_ALL )
    
def printYahooFinanceNews():
    page = requests.get('https://finance.yahoo.com/news/')
    if page.status_code == 200 :
        source = lxml.html.fromstring(page.content)
        return source.xpath('.//a[contains(@class,"js-content-viewer")]/text()') 

def stock_ticker_msg( stock_symbol, live_price, change ):       
    if change < 0 :
        message = printNumber(Fore.RED,  f'{stock_symbol} {live_price:,.2f} '+ u'\N{BLACK DOWN-POINTING TRIANGLE}'+ f' {change:.2f}% ')
    elif change == 0 :
        message = printNumber(Fore.GREEN,f'{stock_symbol} {live_price:,.2f} '+ u'\N{BLACK SQUARE}'+ f' {change:.2f}% ')    
    else:
        message = printNumber(Fore.BLUE, f'{stock_symbol} {live_price:,.2f} '+ u'\N{BLACK UP-POINTING TRIANGLE}'+ f' {change:.2f}% ')   
    
    return message, len(message)
    
def mostActiveStocks(stock_ticker_prices, active_stock_num):
    active_list = si.get_day_most_active() # https://finance.yahoo.com/most-active
    symbols = active_list['Symbol'][:active_stock_num]
    prices = active_list['Price (Intraday)'][:active_stock_num]
    changes = active_list['% Change'][:active_stock_num]
    
    for i in range(len(symbols)) : 
        stock_ticker_prices.append( stock_ticker_msg( symbols[i], prices[i], changes[i] ) )
        
    return len(symbols)

def main():
    """Program entry point."""
   
    term = Terminal()  
    assert term.hpa(1) != u'', ('Terminal does not support hpa (Horizontal position absolute)')

    min_stock_num = 50
    active_stock_num = 50
    
    clearScreen( term )
    printMenu( term )
    
    # top ticker lines
    top_space = int(term.height / 2) - 8 # clock + 1/2 index funds (SP, DOw, ...) 
    top_yPos = top_space + 6
    ticker_total_num = 0
    top_ticker_yPos = 3
    for i in range( 4, 4+top_space, 2):
        printLine( term, i, 0 , term.width ) 
        ticker_total_num += 1
    # bottom ticker lines
    bottom_yPos = int(term.height / 2) + 5 # 1/2 index funds (SP,DOW, ... ) + menu
    for i in range( bottom_yPos, bottom_yPos + top_space, 2):
        printLine( term, i, 0 , term.width )
        
    #              Price | Change | Precent
    # Dow
    # S&P 500
    # Nasdaq
    # NYSE
    # Russell 2000
    # 10-Yr Bond
    index_yPos = top_yPos 
    printIndexTitle( term, index_yPos, 5 , "S&P 500" )
    printDivider( term, index_yPos, 23, 4 )
    printIndexTitle( term, index_yPos, 25 , "Dow 30" )
    printDivider( term, index_yPos, 43, 4 )
    printIndexTitle( term, index_yPos, 45 , "Nasdaq" )
    printDivider( term, index_yPos, 63, 4 )
    printIndexTitle( term, index_yPos, 65 , "NYSE" )
    printDivider( term, index_yPos, 83, 4 )
    printIndexTitle( term, index_yPos, 85 , "Russell 2000" )
    printDivider( term, index_yPos, 103, 4 )
    printIndexTitle( term, index_yPos, 105 , "Bitcoin" )    
            
    resetPosition( term )
     
    # stock tickers
    stock_ticker_prices = [] # most active stocks <- mostActiveStocks()
    
    stock_tickers = []
    stock_flags = []
    stock_symbol_id = []
    for i in range(ticker_total_num*2 + 1):
        stock_symbol_id.append(1)
        if i == 0 :
            stock_flags.append( [False, True,  True] )  # underflow, overflow (True) for the 1st ticker, active/inactive
        else: 
            stock_flags.append( [False, False, False] ) # underflow, overflow
    
    # time-elapsed
    start_time = time.time()
    
    with term.cbreak():
        inp = None
        
        for i in range(ticker_total_num):
            if i % 2 == 0 :                          # width, direction, xPos, yPos, col
                stock_tickers.append(StockTickerLine(term.width, 1,          0, top_ticker_yPos + i*2 )) 
            else : 
                stock_tickers.append(StockTickerLine(term.width,-1, term.width, top_ticker_yPos + i*2 , term.width - 1))
            #stock_tickers[i].append(stock_ticker_prices[0][0])
            #if i != 0 :
            #    stock_tickers[i].setFirstTickerSize(stock_ticker_prices[0][1])
                
        for i in range(ticker_total_num, ticker_total_num*2):
            if i % 2 == 0 :
                stock_tickers.append(StockTickerLine(term.width, 1, 0,          bottom_yPos + 1 + (i-ticker_total_num)*2))
            else : 
                stock_tickers.append(StockTickerLine(term.width,-1, term.width, bottom_yPos + 1 + (i-ticker_total_num)*2, term.width - 1))
            #stock_tickers[i].append(stock_ticker_prices[0][0])
            #stock_tickers[i].setFirstTickerSize(stock_ticker_prices[0][1])
        
        printDateTime( term, 1, 0, 0 )
        
        printIndexPrice( term, '^GSPC' , index_yPos + 2, 5 )
        printIndexPrice( term, '^DJI'  , index_yPos + 2, 25 )
        printIndexPrice( term, '^IXIC' , index_yPos + 2, 45 )   
        printIndexPrice( term, '^NYA'  , index_yPos + 2, 65 )        
        printIndexPrice( term, '^RUT'  , index_yPos + 2, 85 )
        printIndexPrice( term, 'BTC-USD' , index_yPos + 2, 105)
    
        active_stock_num = mostActiveStocks(stock_ticker_prices, active_stock_num)
        stock_tickers[0].append(stock_ticker_prices[0][0])
        
        while inp != 'X':
            #resetPosition( term )
            elapsed_time = round(time.time()-start_time) # seconds
            
            for i in range(len(stock_tickers)):
                if stock_flags[i][1] :  # overflow
                    if not stock_flags[i][2] :
                        stock_tickers[i].append(stock_ticker_prices[0][0])
                        stock_tickers[i].setFirstTickerSize(stock_ticker_prices[0][1])
                        stock_flags[i][2] = True
                    stock_flags[i][0], stock_flags[i+1][1] = stock_tickers[i].write(term);
                    if stock_flags[i][0] :  # underflow
                        #stock_tickers[i].append( stock_ticker_prices[stock_symbol_id[i]][0] )                         
                        if stock_symbol_id[i] >= active_stock_num :
                            stock_symbol_id[i] = 0    
                        stock_tickers[i].append( stock_ticker_prices[stock_symbol_id[i]][0] )
                        stock_symbol_id[i] += 1
            
            # every 15 secs            
            if elapsed_time % 15 == 2: 
                printIndexPrice( term, '^GSPC', index_yPos + 2, 4  )
                printIndexPrice( term, '^DJI' , index_yPos + 2, 25 )
            if elapsed_time % 15 == 6 :
                printIndexPrice( term, '^IXIC', index_yPos + 2, 45 )               
                printIndexPrice( term, '^NYA' , index_yPos + 2, 65 )
            if elapsed_time % 15 == 10 :
                printIndexPrice( term, '^RUT' , index_yPos + 2, 85 )
                printIndexPrice( term, 'BTC-USD' ,index_yPos + 2, 105)                       
            if elapsed_time % 15 == 13 :
                stock_ticker_prices = [] # clear
                active_stock_num = mostActiveStocks(stock_ticker_prices, min(active_stock_num, min_stock_num) )
           
            printDateTime( term, 1, 0, elapsed_time )            
            inp = term.inkey(0.1)
                                
    sys.stderr.write(Style.RESET_ALL)
    sys.stderr.write(term.move_yx(term.height, 0));
    print()

if __name__ == '__main__':
    main()
