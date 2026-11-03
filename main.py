import os
import requests
import json
import time

BOT_TOKEN = "9023581977:AAGFvJTLy7ArrhwAd4vZrimzqClqnSkFR-g"
CHAT_ID = "@richway_crypto"
REF_LINK = "https://www.gate.com"
VIP_CONTACT = "https://t.me/richway_crypto"

def fmt_p(val):
    if val >= 100:
        return f"${val:,.2f}"
    elif val >= 1:
        return f"${val:,.4f}"
    else:
        return f"${val:,.6f}"

def get_market_rankings():
    """從全球無地區限制的合約接口抓取即時數據"""
    try:
        # 單一請求獲取全部 USDT 永續合約行情與費率
        url = "https://api.gateio.ws/api/v4/futures/usdt/tickers"
        res = requests.get(url, timeout=15).json()

        valid_list = []
        for item in res:
            contract = item.get("contract", "")
            # 只篩選 USDT 結算的永續合約
            if not contract.endswith("_USDT"):
                continue

            # 排除成交額低於 300 萬 USDT 的冷門幣
            vol = float(item.get("volume_24h_quote", 0))
            if vol < 3_000_000:
                continue

            fr = float(item.get("funding_rate", 0)) * 100
            price = float(item.get("mark_price", 0))
            if price <= 0:
                price = float(item.get("last", 0))

            chg = float(item.get("change_percentage", 0))
            clean_sym = contract.replace("_USDT", "")

            valid_list.append({
                "symbol": clean_sym,
                "full_symbol": clean_sym + "USDT",
                "price": price,
                "fr": fr,
                "chg": chg
            })

        print(f"成功抓取全市場有效合約幣種數量: {len(valid_list)}")
        return valid_list
    except Exception as e:
        print(f"數據抓取失敗: {e}")
        return []

def send_detailed_signal(coin, is_long=True):
    symbol = coin["symbol"]
    full_symbol = coin["full_symbol"]
    price = coin["price"]
    fr = coin["fr"]
    chg = coin["chg"]

    if is_long:
        direction = "做多 (LONG 🟢)"
        strategy_reason = "空頭資金費率嚴重折價，空方踩踏風險高，留意暴力軋空反彈"
        sl_price = price * 0.970       # -3% 止損
        tp1_price = price * 1.020      # +2% TP1
        tp2_price = price * 1.045      # +4.5% TP2
        tp3_price = price * 1.080      # +8.0% TP3
    else:
        direction = "做空 (SHORT 🔴)"
        strategy_reason = "多頭資金費率極度過熱，槓桿過高，警惕多殺多踩踏"
        sl_price = price * 1.030       # +3% 止損
        tp1_price = price * 0.980      # -2% TP1
        tp2_price = price * 0.955      # -4.5% TP2
        tp3_price = price * 0.920      # -8.0% TP3

    msg = (
        f"🎯 <b>【致富之道 · 智能合約交易訊號】</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>交易標的：</b> <code>#{symbol} / USDT</code>\n"
        f"🧭 <b>操作方向：</b> <b>{direction}</b>\n"
        f"📊 <b>當前價格：</b> <code>{fmt_p(price)}</code> (24H: {chg:+.2f}%)\n"
        f"⚡ <b>建議槓桿：</b> <code>3x - 5x (逐倉 Isolated)</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>分批止盈點位 (Take Profit)：</b>\n"
        f" ├ <b>TP 1：</b> <code>{fmt_p(tp1_price)}</code> (+2.0%)\n"
        f" │  └ <i>建議平倉 50%，同時將止損移至進場價保本</i>\n"
        f" ├ <b>TP 2：</b> <code>{fmt_p(tp2_price)}</code> (+4.5%)\n"
        f" │  └ <i>建議平倉 30%，鎖定核心波段利潤</i>\n"
        f" └ <b>TP 3：</b> <code>{fmt_p(tp3_price)}</code> (+8.0%+)\n"
        f"    └ <i>剩餘 20% 移動止盈，讓利潤奔跑</i>\n\n"
        f"🛑 <b>嚴格防守止損 (Stop Loss)：</b>\n"
        f" └ <b>SL：</b> <code>{fmt_p(sl_price)}</code> (3.0% 空間)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>策略背景：</b>\n"
        f"預測資金費率為 <code>{fr:+.4f}%</code>。{strategy_reason}。\n\n"
        f"⚠️ <i>風險提示：請嚴格執行倉位管理，單筆虧損嚴禁超過總本金 2%！</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📈 TradingView 即時圖表", "url": f"https://www.tradingview.com/symbols/{full_symbol}/"},
                {"text": "⚡ 交易所手續費折抵下單", "url": REF_LINK}
            ],
            [
                {"text": "👑 聯繫管理員 / 升級 VIP 專屬訊號", "url": VIP_CONTACT}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload, timeout=10)
    print(f"發送 {symbol}，Telegram 回覆碼: {res.status_code}")

def main():
    data = get_market_rankings()
    if not data:
        print("未抓取到有效合約數據")
        return

    # 排序：挑出全網費率最高（做空機會）與最低（做多機會）
    sorted_by_fr = sorted(data, key=lambda x: x["fr"], reverse=True)
    top_short = sorted_by_fr[0]
    top_long = sorted_by_fr[-1]

    print(f"發送做空訊號: {top_short['symbol']} (費率: {top_short['fr']:+.4f}%)")
    send_detailed_signal(top_short, is_long=False)
    time.sleep(3)

    print(f"發送做多訊號: {top_long['symbol']} (費率: {top_long['fr']:+.4f}%)")
    send_detailed_signal(top_long, is_long=True)

if __name__ == "__main__":
    main()
