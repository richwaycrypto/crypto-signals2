import requests
import json
import time

BOT_TOKEN = "9023581977:AAGFvJTLy7ArrhwAd4vZrimzqClqnSkFR-g"
CHAT_ID = "-1004491023055"

# 你的商業推廣連結（可替換為你的交易所推薦碼或 VIP 客服連結）
REF_LINK = "https://bingxzone.com/referral-program/JAHJZS?activityId=1633263696958816300"
VIP_CONTACT = "https://t.me/richway_crypto"

def get_market_data(symbol):
    """抓取幣安永續合約最新價格、資金費率、24小時漲跌幅"""
    try:
        # 資金費率與標記價格
        prem_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
        prem_data = requests.get(prem_url, timeout=10).json()
        mark_price = float(prem_data["markPrice"])
        funding_rate = float(prem_data["lastFundingRate"]) * 100

        # 24H 統計數據
        ticker_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
        ticker_data = requests.get(ticker_url, timeout=10).json()
        change_24h = float(ticker_data["priceChangePercent"])

        return mark_price, funding_rate, change_24h
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None, None, None

def send_signal(symbol, price, funding_rate, change_24h, signal_type, is_bullish):
    """發送帶有商業按鈕與精美排版的 Telegram 訊號"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    icon = "🟢" if is_bullish else "🔴"
    clean_sym = symbol.replace("USDT", "")

    # HTML 商業排版訊息
    msg = (
        f"<b>{icon} 【致富之道 · 衍生品情緒雷達】</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>標的幣種：</b> <code>#{clean_sym} / USDT</code>\n"
        f"<b>市場狀態：</b> <b>{signal_type}</b>\n"
        f"<b>當前價格：</b> <code>${price:,.2f}</code>\n"
        f"<b>24H 漲跌：</b> <code>{change_24h:+.2f}%</code>\n"
        f"<b>預測費率：</b> <code>{funding_rate:+.4f}%</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>策略解讀：</b>\n"
    )

    if is_bullish:
        msg += "空頭極度擁擠，合約資金費率嚴重折價，隨時注意軋空暴力反彈機會！"
    else:
        msg += "多頭槓桿過熱，資金費率處於高位，警惕主力多殺多踩踏回踩風險！"

    # 商業導流按鈕（引流至交易所返佣或私密 VIP）
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📈 TradingView 即時圖表", "url": f"https://www.tradingview.com/symbols/{symbol}/"},
                {"text": "⚡ 交易所手續費折抵下單", "url": REF_LINK}
            ],
            [
                {"text": "👑 聯繫管理員 / 升級 VIP 專屬訊號", "url": VIP_CONTACT}
            ]
        ]
    }

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload, timeout=10)

def main():
    # 監控主流幣種列表
    watchlist = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
    
    for symbol in watchlist:
        price, fr, chg = get_market_data(symbol)
        if price is None:
            continue
        
        # 觸發條件（可根據行情微調門檻）
        # 1. 資金費率 >= 0.03% (多頭過熱警報)
        if fr >= 0.03:
            send_signal(symbol, price, fr, chg, "多頭過熱 ↘ 警惕多殺多", is_bullish=False)
            time.sleep(2)
        # 2. 資金費率 <= -0.015% (空頭過度擁擠/潛在軋空)
        elif fr <= -0.015:
            send_signal(symbol, price, fr, chg, "空頭擁擠 ↗ 潛在軋空反彈", is_bullish=True)
            time.sleep(2)

if __name__ == "__main__":
    main()

