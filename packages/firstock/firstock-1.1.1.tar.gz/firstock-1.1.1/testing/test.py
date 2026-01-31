from firstock import firstock
import sys, os
#  
# try:
#     from firstock.ordersNReport.getHoldingsDetailsFirstock.execution import getHoldingsDetails
# except Exception as error:
#     print(error)

try:
    from firstock.ordersNReport.getHoldingsDetailsFirstock import getHoldingsDetails
except Exception as error:
    print(error)


# userId = 'CM2096'

# holdings = getHoldingsDetails(userId=userId)
# print("Holdings Result:", holdings)

login = firstock.login(
    userId='CM2096',
    password='Leaveme@L0ne',
    TOTP='1996',   
    vendorCode='FIRSTOCK_MST_KEY',
    apiKey='Nco@MS7K8t',
)

# login = firstock.login(
#     userId='NP2997',
#     password='Skanda@2025',
#     TOTP='1997',   
#     vendorCode='NP2997_API',
#     apiKey='e55eb28e18ee1337fc0b2705f9b82465',
# )



# login = firstock.login(
#     userId='CM2096',
#     password='Leaveme@L0ne',
#     TOTP='1996',
#     vendorCode='FIRSTOCK_MST_KEY',
#     apiKey='Nco@MS7K8t',
# )
# print(login)


# logout = firstock.logout("SA2898")
# print("logout", logout)
#
# userDetails = firstock.userDetails("SA2898")
# print(userDetails)
#
# placeOrder = firstock.placeOrder(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="ITC-EQ",
#     quantity="1",
#     price="300",
#     product="I",
#     transactionType="B",
#     priceType="LMT",
#     retention="DAY",
#     triggerPrice="",
#     remarks="Python Package Order"
# )
# print("placeOrder", placeOrder)
#
# orderMargin = firstock.orderMargin(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="ITC-EQ",
#     quantity="1",
#     priceType="LMT",
#     product="C",
#     price="350",
#     transactionType="B"
# )
# print("orderMargin", orderMargin)
#
# orderBook = firstock.orderBook("SA2898")
# print("orderBook",orderBook)
#
# cancelOrder = firstock.cancelOrder(
#     userId= "SA2898",
#     orderNumber="25063000011862"
# )
# print("cancelOrder", cancelOrder)
#
# modifyOrder = firstock.modifyOrder(
#     userId= "SA2898",
#     orderNumber="25070100015934",
#     quantity="1",
#     price="418",
#     triggerPrice="0",
#     tradingSymbol="IDEA-EQ",
#     priceType="LMT",
#     retention = "DAY",
#     mkt_protection= "0.5",
#     product= "C",
# )
# print(modifyOrder)
#
# singleOrderHistory = firstock.singleOrderHistory(
#     userId= "SA2898",
#     orderNumber="25063000011911"
# )
# print(singleOrderHistory)
#
# tradeBook = firstock.tradeBook("SA2898")
# print("tradeBook",tradeBook)
#
# positionBook = firstock.positionBook("SA2898")
# print("positionBook", positionBook)
#

# convertProduct = firstock.productConversion(
#     userId="CM2096",
#     transactionType="B",
#     tradingSymbol="ITC-EQ",
#     quantity="1",
#     product="C",
#     previousProduct="I",
#     positionType="DAY",
#     exchange="NSE",
#     msgFlag="1"  # Buy and Day

# )
# print(convertProduct)
#
# holdings = firstock.holdings("SA2898")
# print("holdings", holdings)
#
# limits = firstock.limit("SA2898")
# print("limits", limits)
#
# basketMargin = firstock.basketMargin(
#     userId="SA2898",
#     exchange="NSE",
#     transactionType="B",
#     product="C",
#     tradingSymbol="RELIANCE-EQ",
#     quantity="1",
#     priceType="MKT",
#     price="0",
#     BasketList_Params=[
#         {
#             "exchange": "NSE",
#             "tradingSymbol": "IDEA-EQ",
#             "quantity": "1",
#             "transactionType": "B",
#             "price": "0",
#             "product": "C",
#             "priceType": "MKT"
#         }
#     ]
# )
# print(basketMargin)
#
# getSecurityInfo = firstock.securityInfo(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="NIFTY"


# )
# print(getSecurityInfo)
#
# getQuotes = firstock.getQuote(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="NIFTY"
# )
# print(getQuotes)
#
# getIndexList = firstock.indexList(
# userId="SA2898",
# )
# print(getIndexList)
#
# optionChain = firstock.optionChain(
#     userId= "SA2898",
#     exchange="NFO",
#     symbol="NIFTY",
#     strikePrice="23150",
#     expiry= "03JUL25",
#     count="5"
#             )
# print(optionChain)
#
#
# searchScrips = firstock.searchScrips(
#     userId= "SA2898",
#     stext="ITC"
# )
# print(searchScrips)
#
# getQuoteLtp = firstock.getQuoteltp(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="RELIANCE-EQ"
# )
# print(getQuoteLtp)
#
# mQ = firstock.getMultiQuotes(
#     userId="SA2898",
#     dataToken=[
#         {
#             "exchange": "NSE",
#             "tradingSymbol": "Nifty 50"
#         },
#         {
#             "exchange": "NFO",
#             "tradingSymbol": "NIFTY03APR25C23500"
#         }
#     ]
# )
# print(mQ)
#
# mQLTP = firstock.getMultiQuotesltp(
#     userId="SA2898",
#     dataToken=[
#         {
#             "exchange": "NSE",
#             "tradingSymbol": "Nifty 50"
#         },
#         {
#             "exchange": "NSE",
#             "tradingSymbol": "Nifty Bank"
#         }
#     ]
# )
# print(mQLTP)
#
# bc = firstock.brokerageCalculator(
#     userId="SA2898",
#     exchange="NFO",
#     tradingSymbol="RELIANCE27FEB25F",
#     transactionType="B",
#     product="M",
#     quantity="500",
#     price="125930",
#     strike_price="0",
#     inst_name="FUTSTK",
#     lot_size="1"
# )


# print(bc)
#
# fExpiry = firstock.getExpiry(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="NIFTY"
# )


# print(fExpiry)
#
# timePriceSeries = firstock.timePriceSeries(
#     userId="SA2898",
#     exchange="NSE",
#     tradingSymbol="NIFTY",
#     startTime="09:15:00 23-04-2025",
#     endTime="15:29:00 23-04-2025",
#     interval="1mi"
# )
# print(timePriceSeries)


# holdings = firstock.getHoldingsDetails(userId = 'CM2096')
# print("Holdings Result:", holdings)


# from firstock import firstock
# import sys, os

# try:
#     from firstock.ordersNReport.getHoldingsDetailsFunctionality.execution import getHoldingsDetails
# except Exception as error:
#     print("Import Error:", error)

# if __name__ == "__main__":
#     # Login test to set the jKey in config.json (using the official SDK method)
#     login = firstock.login(
#         userId='CM2096',
#         password='Leaveme@L0ne',
#         TOTP='1996',
#         vendorCode='FIRSTOCK_MST_KEY',
#         apiKey='Nco@MS7K8t',
#     )
#     print("Login Result:", login)

#     # Holdings test
#     userId = 'CM2096'
#     holdings = getHoldingsDetails(userId=userId)
#     print("Holdings Result:", holdings)