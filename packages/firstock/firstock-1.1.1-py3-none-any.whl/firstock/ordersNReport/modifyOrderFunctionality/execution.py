from firstock.ordersNReport.modifyOrderFunctionality.functions import *


class FirstockModifyOrder:
    def __init__(self, qty, orderNumber, trgprc, product, mkt_protection, prc, tradingSymbol, priceType,userId, retention):
        self.modifyOrder = ApiRequests()
        self.qty = qty
        self.orderNumber = orderNumber
        self.trgprc = trgprc
        self.prc = prc
        self.tradingSymbol = tradingSymbol
        self.priceType = priceType
        self.userId=userId
        self.retention=retention
        self.mkt_protection= mkt_protection
        self.product = product

    def firstockModifyOrder(self):
        result = self.modifyOrder.firstockModifyOrder(self.qty, self.orderNumber, self.trgprc, self.prc,
                                                      self.tradingSymbol, self.priceType, self.userId, self.retention, self.product, self.mkt_protection)
        return result
