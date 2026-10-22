# Campus Customs — Usability Improvements (Problem 9)

Goal: 2 front-end and 2 agent/backend usability improvements. For each: **what was added** and **why it helps a Campus Customs shopper or the business**. This file was written *before* building and updated as each piece was built and tested.

| # | Type | Improvement | Status |
|---|---|---|---|
| B1 | Backend | Clear chat + 30-day chat retention | ✅ Built in Problem 8 (follow-ups) |
| B2 | Backend | Customer data protection: less data to the AI, sensitive info removed, login lockout | ✅ Built and tested |
| F1 | Front end | "Ask Bulldog about this item" + page-aware quick questions | ✅ Built and tested |
| F2 | Front end | Mobile- and keyboard-friendly chat | ✅ Built and tested |
| F3 | Front end (owner request) | "Shop by" collection filters: Sports, Schools, Colleges, Relatives | ✅ Built and tested |
| F4 | Front end (owner request) | Map + "open in Google / Apple Maps / Waze / copy address" on About Us | ✅ Built and tested |
| S1 | Front + back end | Shopping cart (honest server-priced totals; checkout clearly marked as a demo) | ✅ Built and tested |
| S2 | Backend | Chat rate limit (20 messages/minute) + 200-message saved-history cap | ✅ Built and tested |
| S3 | Front end + agent | Size & fit guide (sample, based on Port & Company charts) | ✅ Built and tested |
| S4 | Front end | Sort (price, name) + price range + in-stock-only filters | ✅ Built and tested |
| S5 | Front + back end + agent | "Notify me when back in stock" | ✅ Built and tested |
| S6 | Front + back end | My Account page (profile, restock alerts, chat history, sign out) | ✅ Built and tested |
| S7 | Backend / setup | Clear setup message + `data/README.md` for a fresh GitHub clone | ✅ Built and tested (found by the pre-push checks) |
| P10-1 | Front end | Look & feel matched to yalebulldogblue.com (Open Sans, white header, cream footer, #00366b buttons) | ✅ Built and tested |
| P10-2 | Front end | Home hero: the real site's lifestyle banner (owner-provided); navy background if it's missing | ✅ Built and tested |
| P10-3 | Backend + agent | "Boola Boola" → one Boola#### code per logged-in shopper per year | ✅ Built and tested |
| P10-4 | Front + back end | Discount code box in the cart (7-day shelf life) | ✅ Built and tested |
| P10-5 | Front end | Bulldog icon randomly winks, barks or licks on click | ✅ Built and tested |
| — | Wording (owner request) | Chat status "Chat auto saved to your account for 30 days"; button "Clear Chat" | ✅ Done |

---

## B1. Clear chat + 30-day chat retention (backend)

**What was added**
- A subtle **Clear Chat** button opposite **Send** that asks for confirmation. For guests it clears the in-tab chat. For logged-in shoppers it deletes their saved history (`DELETE /api/chat/history`). It also clears Bulldog's picks from the page.
- A **30-day clock** per shopper: saved history lasts up to 30 days from its first message, then is deleted automatically (at startup, before loading, and before saving). After a Clear, the next message starts a new 30 days. The 22 course sample messages are flagged `is_sample` and kept for learning.

**Why it helps**
- *Shopper:* control over their own data, a fresh start when they want one, and no surprise "old" conversations months later. The confirmation and the out-of-the-way placement prevent accidental deletes.
- *Business:* keeping chat logs only as long as they're useful lowers privacy risk and storage. It's also a clear, honest policy Bulldog can explain when asked.

*Tested in Problem 8. See `output/harness.md` → "Retention and clearing". Later extended with a 200-message cap (see S2).*

---

## B2. Customer data protection (backend)

**The problem we found:**
- In Problem 8, every chat turn sent the logged-in shopper's **full name and email** to the AI model provider (Portkey → Sol 5.6, called with our API key). The API key itself never left the server, but customer data travelled with every request.
- Shoppers sometimes paste things that should never be in a chat, such as a card number, a phone number or a password. Those were sent to the AI **and saved in `chat_messages` for up to 30 days**.
- Login had no limit on password guesses.

**What was added:**
1. **Data minimization** (`agent.py`, `tools.py`, `models.AccountInfo`):
   - The AI's instructions now carry the shopper's **first name only**.
   - `get_my_account` returns the first name, **last initial** and a **masked email** (`ad•••@yale.edu`).
   - The full email and last name stay on our server. Bulldog still knows who's chatting and can confirm the account ("Sam Q., sa•••@example.test").
2. **Sensitive-info redaction** (new `backend/privacy.py`):
   - Before a message reaches the AI *or* the database, these are replaced with labels: card numbers (13–19 digits, Luhn-checked so order numbers aren't caught), SSNs, phone numbers, email addresses, and "password is …" phrases.
   - Guest history sent from the browser is cleaned the same way.
   - The response includes `redacted` and `safe_message`. The chat replaces what the shopper typed with the cleaned text and shows "🔒 For your security, we removed a card number from your message."
   - Bulldog explains the removal and reminds shoppers never to share payment details. The server log records only the *kind* removed ("chat redacted: card number"), never the value.
3. **Login lockout** (`auth.py`):
   - After **5 wrong passwords for an email within 15 minutes**, further attempts are refused with HTTP 429, "Too many login attempts. Please wait N minutes…", even with the correct password.
   - A successful login resets the count. Other accounts aren't affected.

**Why it helps:**
- *Shopper:* their email and surname aren't shared with an outside AI company. A card number pasted by mistake is never sent out or stored. Their account can't be brute-forced.
- *Business:* less customer data leaves our systems, so less is at risk if a vendor is breached. It also reduces payment-card compliance exposure (card numbers never land in our logs or database), and it builds trust in the Campus Customs brand.

**Tested:**

| Test | Result |
|---|---|
| Unit: card `4111 1111 1111 1111`, phone `(203) 555-0142`, SSN, email, "my password is …" | ✅ All replaced with labels |
| Unit: shop text "2025 Yale vs Harvard T-Shirt in M under $40", "Order #123456… $68", card number failing Luhn | ✅ Left unchanged (no false positives) |
| Guest pastes a card number | ✅ `redacted: ["card number"]`; Bulldog: "the card number was removed — please never share payment details in chat" |
| Logged-in shopper sends a phone number | ✅ Saved DB row reads `Text me at [phone number removed] when…`. Database search for the card/phone digits: **0 rows** |
| **Everything sent to the model provider in one real turn** (captured with `capture_run_messages`) | ✅ Contains first name "Sam" only; **no full email, no last name, no phone, no card number** |
| "What email and name am I logged in with?" | ✅ "Sam Q., sa•••@example.test… the full email isn't shared with chat for privacy; it's the address you use to log in" |
| Server log | ✅ Only "chat redacted: card number" / "phone number"; no digits |
| 6 wrong passwords | ✅ 401 ×5, then **429** |
| Correct password while locked | ✅ Still 429, "Please wait 15 minutes" |
| A different account during the lockout | ✅ Unaffected (normal 401) |

*Fix found during testing:* Bulldog first told a shopper to "view it in your account on the website", but there is no account page. That wording came from my own tool description. I corrected the tool and the prompt, and the retest answered correctly.

**Further steps for a real deployment (not built):**
- HTTPS with `secure=True` cookies.
- Turn off or limit request logging in the Portkey dashboard, and confirm the model provider's data-retention terms.
- Move the lockout to the database or Redis if there's more than one server.
- Add a privacy notice to the chat.

---

## F1. "Ask Bulldog about this item" + page-aware quick questions (front end)

**What was added:**
- A **"🐶 Ask Bulldog about this item"** button on every product page, under Add to Cart. It opens the chat with the message box ready. (`chatEvents.ts` lets any page open the chat.)
- **Quick-question chips that match the page** (`ChatWidget.quickQuestions`):
  - *Product page:* "Is this in stock in my size?", "What colors does this come in?", "Show me similar items"
  - *Category page* (e.g. Hoodies): "Hoodies under $60", "Navy hoodies", "Which hoodies are in stock in M?"
  - *Elsewhere:* general starters
- On a product page the chips **stay in a row above the message box** during the conversation, so the next question is one tap away.
- Because Bulldog already gets the page context (Problem 8), "this" always means the item on screen.
- A question about the item already on screen **doesn't open a redundant "Bulldog's picks" panel** above it. New suggestions, such as similar items, still appear there.

**Why it helps:**
- *Shopper:* answers about the exact item they're looking at in one tap, without typing the product name, which is easier on a phone.
- *Business:* more shoppers get their size and color questions answered on the product page, the moment they're deciding. That should mean fewer abandoned visits and more "similar items" discovery.

**Tested:**

| Test | Result |
|---|---|
| Button on the Baseball Left Chest Crewneck page | ✅ Chat opens, message box focused |
| Product-page chips | ✅ The 3 item questions |
| Tap "What colors does this come in?" | ✅ "comes in navy and white" (DB: navy, white) |
| Chips row after the answer | ✅ Still shown above the message box |
| Question about the on-screen item | ✅ No redundant picks panel *(found in testing and fixed)* |
| Tap "Show me similar items" | ✅ Suggests Yale Sports Crewneck Baseball in Bulldog's picks |
| Hoodies category page chips | ✅ "Hoodies under $60", "Navy hoodies", "Which hoodies are in stock in M?" |

---

## F2. Mobile- and keyboard-friendly chat (front end)

**What was added:**
- **Phones (≤ 560 px wide):**
  - The chat opens **full screen** instead of a small box covering the page.
  - The page behind it stops scrolling, and the floating button hides while the chat is open (the ✕ closes it).
  - The message box uses a 16 px font so iPhones don't zoom in when typing.
- **Keyboard and accessibility:**
  - The message box is **focused automatically** when the chat opens.
  - **Escape** closes the chat and **returns focus to the Bulldog button**, so keyboard and screen-reader users don't lose their place.
- Desktop keeps the 360 px panel.

**Why it helps:**
- *Shopper:* many students and parents shop on their phones. A full-screen chat is readable and easy to type in, rather than a cramped box over the page.
- *Business:* a better mobile experience means more mobile visitors actually use Bulldog (and buy). Keyboard support also widens the audience and meets basic accessibility expectations.

**Tested:**

| Test | Result |
|---|---|
| Phone 375×812: open chat | ✅ Panel 375×812 at (0,0); page scroll locked; button hidden; box focused; 16 px font |
| Phone: Escape | ✅ Chat closed; page scroll restored; focus back on the Bulldog button *(first attempt didn't restore focus because the button was still hidden; fixed by focusing after the panel closes)* |
| Desktop 1280 px | ✅ 360×559 panel; page still scrolls; Escape closes |
| Console / build / tool checks | ✅ No errors; production build OK; 2,249 / 0 failures |

Test accounts (`@example.test`) were deleted afterwards. The database has 4 users and the 22 sample chat messages, with no card or phone digits stored anywhere.


---

## Owner-requested additions (after reviewing F1/F2)

### F3. "Shop by" collection filters: Sports, Schools, Colleges, Relatives

**What was added:**
- A second filter row on the Products page, **"Shop by: Sports 34 · Schools 13 · Colleges 19 · Relatives 12"**, under the existing type filters (Hoodies, Crewnecks…). It mirrors the "Browse" menus on yalebulldogblue.com.
- **How it works:**
  - Collections combine with type and search (e.g. *Sports · Hoodies* = 13), and the page title shows both.
  - Clicking an active collection again turns it off, and there's a **Clear filters** link. The URL keeps the filters (`?collection=Sports&category=Hoodies`), so a filtered page can be shared or bookmarked.
- **How products are grouped** (`tools.COLLECTIONS`):
  - By whole words in the product **name** (e.g. "Saybrook", "School of", "Yale Mom", "Baseball"). Descriptions aren't used, because non-sports items mention things like "football helmets".
  - No product is in two collections. The 24 general Yale items (Champion, Brooks Brothers, vintage Bulldog…) appear under *All*.
  - "Crew Left Chest Hoodie" counts as Sports (crew = rowing). This is grouping only; no product data was changed.
- **Where it's available:** API `GET /api/collections` and `/api/products?collection=…`. The agent's `search_products` also accepts `collection`, so "show me residential college gear" or "something for my mom" uses the same groups. The Home page's "All colleges →" link now opens the Colleges collection.
- **Empty combinations explain themselves:** "We don't have any hoodies in Colleges right now. **See all Colleges**", instead of "Try a different search".

**Why it helps:**
- *Shopper:* most Yale shoppers come with an affiliation in mind (their team, their college, their grad school, or a gift for Mom or Grandpa). One tap narrows 102 items to the right 12–34.
- *Business:* matches how the real store merchandises (Residential Colleges, Sports, Relatives, Graduate & Professional Schools) and makes gift shopping (Relatives) easy to find.

**Tested:**

| Test | Result |
|---|---|
| Chips and counts | ✅ Sports 34, Schools 13, Colleges 19, Relatives 12 |
| Each collection | ✅ Correct count; first items e.g. Baseball Left Chest Crewneck, The Forest School Hoodie, Davenport College Crewneck, Yale Brother Crewneck |
| Sports + Hoodies | ✅ Title "Sports · Hoodies", 13 products, URL `?category=Hoodies&collection=Sports` |
| Click Sports again | ✅ Removed; back to Hoodies |
| Colleges + Hoodies (no such items) | ✅ "We don't have any hoodies in Colleges right now. See all Colleges" → 19 products *(message improved during testing)* |
| API: Relatives + Hoodies | ✅ The 6 relative hoodies |
| Regression: tool checks | ✅ 2,249 / 0 failures |

### F4. Map and "open in your maps app" on About Us

**What was added:**
- Under **Come Visit Us!** (Yale Bulldog Blue by Campus Customs, 57 Broadway, New Haven, CT 06511):
  - an **embedded Google map** (keyless embed, loads lazily)
  - **"Open directions in:"** buttons for **Google Maps**, **Apple Maps** and **Waze**, each opening in a new tab or the installed app on a phone
  - **Copy address**, for any other app ("Copied ✓" confirms)
- The links use `rel="noopener noreferrer"`.

**Why it helps:**
- *Shopper:* parents and visitors can get directions in one tap with the app they already use, including Apple Maps on iPhone.
- *Business:* the custom-order and on-site production story only works if people can find the store, so this drives in-person visits for custom orders.

**Tested:**

| Test | Result |
|---|---|
| Map and buttons render under "Come Visit Us!" | ✅ Map frame 319×240; 3 app buttons + Copy address |
| Link targets | ✅ Correct encoded address; open in a new tab; `noopener noreferrer` |
| Google, Apple, Waze URLs | ✅ All respond 200 |
| Google embed allowed inside our page | ✅ The final embed page has no `X-Frame-Options` (only Google's redirect step does), so it displays in normal browsers |
| Map displays in a regular browser | ✅ Confirmed by the owner at `http://localhost:5174/about`. (The in-app preview browser blocks outside websites, so it shows blank only there.) |

### Wording tweaks
- Chat status (logged in): **"Chat auto saved to your account for 30 days"**. Guests still see "Guest chat · not saved".
- The clear button is now **"Clear Chat"**, and Bulldog's prompt refers to it by that name.
- ✅ Checked in the browser with a test account (deleted afterwards).


---

## Shop features round (owner-approved recommendations 4–9)

### S1. Shopping cart

**What was added:**
- **Add to Cart works.** Pick a size and a quantity (up to the stock, max 10), then Add to Cart. You see "✓ Added 2 × Baseball Left Chest Crewneck (M) to your cart. **View cart →**".
- The top bar shows **🛒 Cart** with the item count.
- The cart is saved in the browser (`CartContext`, localStorage) and holds **only product, size and quantity**.
- **Cart page (`/cart`):** each line has an image, a name linking to the product, size, unit price, a quantity picker, Remove and a line total, plus an order summary with subtotal.
- **Prices and stock are re-checked on the server every time** (`POST /api/cart/quote`): the browser never supplies a price. Quantities are capped at what's in stock, and lines are flagged "Only 2 available in XXL", "Sold out in XS" or "no longer available".
- **Checkout** is honest: "Online checkout isn't connected yet in this demo store, so no payment is taken. To buy these items, visit us at 57 Broadway, New Haven…". No card details are ever collected.
- **Bulldog** knows about the cart: it points shoppers to Add to Cart, says it can't add items itself, and never promises shipping.

**Why it helps:**
- *Shopper:* can collect items, see a real total, and isn't misled by a button that did nothing.
- *Business:* the core retail flow, with totals that can't be tampered with. When payments are added later, only checkout needs building.

**Tested:**

| Test | Result |
|---|---|
| API quote with a fake `"price": 1` for Morse 1/4 Zip ×2 | ✅ Priced at the DB's **$72.00** → $144 (tampering ignored) |
| Tennis hoodie XXL ×5 (DB stock 2) | ✅ Capped at 2: "Only 2 available in XXL" |
| Baseball crewneck XS (DB stock 0) / unknown product | ✅ "Sold out in XS" / "no longer available", $0 |
| Product page: M, qty 2, Add to Cart | ✅ Confirmation shown; top bar "Cart 2" |
| Cart page: 2 × $58 + 1 × $45 | ✅ Subtotal **$161.00** |
| Change qty to 3 / remove the hoodie | ✅ **$219.00** / **$174.00**; top bar count updates |
| Checkout | ✅ Demo notice; no payment fields |
| Bulldog: "Can you add it to my cart?" | ✅ "I can't add it for you… click **Add to Cart**… Online checkout isn't connected yet…" |

### S2. Chat rate limit + saved-history cap

**What was added:**
- **20 chat messages per minute per visitor** (`store.chat_rate_limited`; visitor = account if logged in, otherwise IP address).
- Message 21 gets HTTP 429 *before the AI is called*: "You're sending messages too quickly. Please wait N seconds and try again." The chat shows that message.
- **Cap of 200 saved messages per shopper** (`memory.MAX_SAVED_MESSAGES`). When a new exchange goes past 200, the oldest are deleted. This works alongside the 30-day clock.

**Why it helps:**
- *Business:* a script or bored visitor can't run up the Portkey AI bill or flood the database. Each visitor costs at most 20 AI calls a minute.
- *Shopper:* normal shoppers never notice, and history stays a manageable size.

**Tested** (in-process, with the AI call stubbed so no cost was spent):

| Test | Result |
|---|---|
| 21 messages from one visitor | ✅ 20 × 200, then **429**; **20** AI calls, not 21 |
| A different visitor at the same time | ✅ Unaffected (200) |
| 220 saved messages for one shopper | ✅ **200** kept; oldest kept is message 11, newest is the latest |

### S3. Size & fit guide

**What was added:**
- **📏 Size guide** next to "Size" on every product page opens a dialog (Escape or click outside to close). It shows the chart for **this item's type first**, labeled "This item".
- **Content (`backend/size_guide.json`, served at `/api/size-guide`):**
  - Garment measurements (width, length, sleeve, in inches) for S–XXL.
  - The chest range each size fits (S 35–37 … XXL 47–49).
  - How to measure.
  - A fit note: adult sizes XS–XXL; not labeled men's or women's except the two "Men's" items; women may prefer one size down.
- **Source:** Port & Company **PC54** (T-shirts) and **PC78** (crewneck, used for sweatshirts, hoodies, quarter-zips, long sleeves and jackets) as listed by Merchloop. Several of our products are printed on Port & Company blanks. It's **labeled as a sample guide**, and the source doesn't publish **XS**, so XS shows "Not published" rather than an invented number.
- **Bulldog tool `get_size_guide`:** answers "men's or women's?" and "what size should I get?" from this guide, and says brands vary.

**Why it helps:**
- *Shopper:* answers the #1 question before buying apparel online, including the men's/women's question you asked.
- *Business:* fewer wrong-size purchases and returns, and fewer sizing questions for staff.

**Tested:**

| Test | Result |
|---|---|
| Guide on Baseball Left Chest Crewneck | ✅ Sweatshirt chart first ("This item"); M = 22 / 29 / 35.12, fits 38–40; XS "Not published" |
| Escape closes the guide | ✅ |
| Bulldog: "Men's or women's? Size for a 39-inch chest?" (Morse 1/4 Zip page) | ✅ Called `get_size_guide` → "adult sizing, not labeled men's or women's… **39-inch chest points to M** (38–40)… brands can fit differently" |

### S4. Sort and price filters on Products

**What was added:** a bar under the filters with:
- **Sort by:** Featured, Price low→high, Price high→low, Name A→Z
- **Price:** Any, Under $40, $40–$60, $60–$80, Over $80
- **In stock only**

These combine with type, collection and search, are kept in the URL (shareable), and are cleared by **Clear filters**.

**Why it helps:**
- *Shopper:* the standard way to shop on a budget or find what's available now.
- *Business:* faster path to purchase, and price-based browsing helps gift buyers.

**Tested:**

| Test | Result |
|---|---|
| Price low→high | ✅ All 102 in ascending order ($32 … $98) |
| $40–$60 + high→low | ✅ **33** products (DB: 33), prices $45–$58, descending |
| Then Name A→Z (real form fill) | ✅ Alphabetical; URL `?sort=name&price=40-60&instock=1` keeps the other filters |
| In stock only | ✅ Works (every product currently has at least one size in stock, so the count is unchanged) |

*Note:* an early automated test made the filters look broken. That was my test script changing values faster than the page updated; re-testing step by step and with real form input showed the page works.

### S5. "Notify me when back in stock"

**What was added:**
- **Sold-out sizes can now be selected** (they're still crossed out). Selecting one shows "Sold out in XS" and a **🔔 Notify me** box:
  - Guests type an email.
  - Logged-in shoppers get one button, "Notify me at their account email".
- Saved in a new **`restock_requests`** table (product, size, email, user, created, notified_at). It's de-duplicated and **only accepted for sizes that are actually sold out** (an in-stock size gets "Good news: … in stock in M, so you can order it now").
- **Logged-in shoppers' requests always use their account email**, even if a different one is sent. That stops anyone signing other people up.
- **Bulldog tool `request_restock_alert`:** a logged-in shopper can just ask ("let me know when it's back"), and Bulldog confirms with the masked email. Guests are pointed to the button.
- **Honest scope:** this project *saves* the requests for the shop to email. It doesn't send email itself, and Bulldog doesn't promise when stock returns.

**Why it helps:**
- *Shopper:* no need to keep checking back.
- *Business:* turns a lost sale into a mailing list of ready buyers per product and size, and shows which sold-out sizes are worth restocking first.

**Tested:**

| Test | Result |
|---|---|
| Guest: XS (sold out) + email | ✅ 201; "✓ We'll email guest.browser@example.test when XS is back in stock." |
| Guest: M (in stock) | ✅ Refused: "Good news… in stock in M" |
| Guest: bad email | ✅ "Please enter a valid email address." |
| Logged in, request body contains someone else's email | ✅ Saved with the **account** email |
| Bulldog (logged in): "Do you have this in XS? …let me know when it's back?" | ✅ `check_stock` → `request_restock_alert` → "sold out in XS… signed you up… at ka•••@example.test… no timing is guaranteed"; row saved |

### S6. My Account page

**What was added:**
- **"Hi, <name>"** in the top bar now links to **My Account** (`/account`; logged-out visitors are sent to Log In). It shows:
  - **Profile:** name, email, member since; **Sign Out**
  - **Restock alerts:** linked products and sizes, with **Cancel**
  - **Chat history with Bulldog:** saved messages, with a note that chats are kept for 30 days / up to 200 messages, and **Clear Chat History**
- **Backend:** `GET /api/account`, `GET /api/restock-alerts`, `DELETE /api/restock-alerts/{id}`. All require login and only touch the shopper's own data.
- Bulldog's prompt now sends shoppers to **My Account** to see their full email. The earlier "there's no account page" rule is removed.

**Why it helps:**
- *Shopper:* one place to see and control what the shop knows about them (alerts, chat history), which builds trust.
- *Business:* a home for future order history, and a clear place for privacy controls.

**Tested:**

| Test | Result |
|---|---|
| "Hi, Kai" link → My Account | ✅ Profile (Kai Moss, email, member since 10/21/2026), 2 alerts, saved chat |
| Cancel an alert | ✅ 2 → 1 on the page and on the server |
| Sign Out from My Account | ✅ Goes to Home, logged out *(first went to Log In; fixed and retested)* |
| `/api/account` when logged out | ✅ 401 |

**Regression after this round:** `check_agent_tools.py` 2,249 / 0 failures; production build OK; no console errors except the expected 401 from my logged-out check. Test accounts, alerts and chats (`@example.test`) were deleted; test carts were cleared.


### S7. Clear setup message for a fresh GitHub clone

**What was added:**
- **The problem:** the database and product photos are deliberately left out of the GitHub repo. So on a fresh clone, `uvicorn main:app` crashed with an unclear Python error (`Directory '…/data/products' does not exist`).
- **`backend/main.py`** now checks for the data at startup. If it's missing, it stops with plain instructions:
  ```
  Campus Customs data not found: data/campus_customs_clean.db, data/products.
  Put campus_customs.db and the products/ image folder in Homework 4/data/, then run
      python scripts/clean_db.py
  to build data/campus_customs_clean.db. See data/README.md.
  ```
- **New `data/README.md`** (committed): explains which files go in `data/`, why they aren't in the repo, and the one command that builds the cleaned database. It also means the `data/` folder exists in a fresh clone.

**Why it helps:**
- *Grader / developer:* anyone cloning the project knows exactly how to get it running, instead of debugging a stack trace.
- *Business:* keeps customer data and production images out of the public repo, without making the project hard to set up.

**Tested** (on a scratch fresh clone; nothing committed):

| Test | Result |
|---|---|
| Fresh clone, no data → start the backend | ✅ The clear message above (was a stack trace before the fix) |
| Add `campus_customs.db` + `products/` → `python scripts/clean_db.py` | ✅ "Wrote campus_customs_clean.db with 136 field changes" |
| `scripts/check_agent_tools.py` on the fresh clone | ✅ 2,249 checks / 0 failures |
| `uvicorn main:app` from `backend/` | ✅ Health OK, 102 products, images served, database not downloadable (404) |
| Real project after the change | ✅ Starts normally |


---

## Problem 10: Style and delight

### P10-1. Look & feel matched to yalebulldogblue.com

**What was added:**
- **The real site's theme values**, read from its Shopify theme settings (CSS variables in the page source):
  - body *and* headings use **Open Sans**; headings are **UPPERCASE at normal weight**
  - text **#1d1d1d**; **white header** with dark text
  - buttons **#00366b** (hover **#1a4a7a**) in sentence case
  - links **#046e82**; light greys **#f6f6f6 / #f4f4f4**
  - **cream footer #f5f3ed**; sale red **#f04f36**
- **Applied as one "Problem 10 theme" block** at the end of `index.css` (easy to review or revert).
- **Open Sans is self-hosted** through the `@fontsource/open-sans` npm package, so the page makes no Google Fonts request.
- **Notable changes:**
  - blue header → white header with a navy logo and dark menu
  - serif bold headings → Open Sans uppercase
  - bordered cards → clean cards on light grey
  - navy footer → cream footer
  - outlined header buttons; red "Sold out" badge
- **Product names stay in normal case**, as on retail sites. Only section headings are uppercase.

**Why it helps:**
- *Shopper:* the shop looks and feels like the official Yale Bulldog Blue store, which builds trust and familiarity.
- *Business:* consistent branding across the real store and this site.

**Tested:**

| Test | Result |
|---|---|
| Computed styles | ✅ body/heading font "Open Sans" (loaded); text rgb(29,29,29); header white; button rgb(0,54,107), not uppercase; footer rgb(245,243,237) |
| Desktop and phone screenshots | ✅ White header, uppercase headings, cream footer, phone menu works |
| *Fixes found in testing* | Product names became uppercase → set back to normal case. The **Log Out button text was invisible** (navy on navy) → fixed (outlined) |

### P10-2. Home hero: the real site's lifestyle banner

**What was added (final version):**
- **The image:** the **lifestyle banner from yalebulldogblue.com**, provided by the owner. It shows smiling students walking on campus in Yale tees and sweatshirts, with the built-in **YALE BULLDOG BLUE · Officially Licensed Merchandise** logo. Saved as `frontend/public/hero/yale-bulldog-blue-banner.webp` (2000×791, 128 KB).
- **Layout, matching the real site:** the banner is shown **whole, at full width, with no cropping or text over it** (so the logo and faces stay clear). The headline ("Bring Tradition with you wherever you go."), "Official Yale Merch." and the two buttons sit in a white band **below** it.
- **Kept out of GitHub** like the product photos: `.gitignore` has `frontend/public/hero/yale-bulldog-blue-banner.*`.
- **Fresh-clone fallback (owner's choice):** if the banner file is missing, `HeroImage` shows the **original navy Yale-blue hero** with the headline in white. No other image is used.

**History (how we got here):**
1. **First:** 7 s of the Homework 3 ad video, then a still. The owner noted it was filmed **under a highway** and didn't reflect Yale life.
2. **AI generation:** Sora 2 video and AI image models were tried through Portkey and **blocked**. The course key only routes to one text model, so nothing was generated or charged.
3. **Next:** an original **vector illustration** of a Gothic campus with students in catalogue merch. The owner preferred photographic imagery like the real site's ("beauty is in the eye of the beholder").
4. **Final:** the owner provided the real site's banner and chose to use it, kept out of GitHub. At the owner's request, the fallback is the original navy background, and the illustration was **deleted**.

**Why it helps:**
- *Shopper:* the same warm, real-photo welcome as the official store, with the brand logo front and center.
- *Business:* brand consistency with yalebulldogblue.com, and production imagery stays out of the public repo.

**Tested:**

| Test | Result |
|---|---|
| Desktop 1280×800 | ✅ Banner loads (2000×791) and shows whole at 1265×500, no crop; headline band below |
| Phone 375×812 | ✅ Full banner under the header; headline and buttons below |
| Banner missing (simulated fresh clone) | ✅ Navy gradient hero, white headline, no image; banner restored afterwards and loads normally |
| Git-ignore | ✅ `frontend/public/hero/yale-bulldog-blue-banner.*` |
| Console / build | ✅ No errors; production build OK |

### P10-3. "Boola Boola" discount code

**What was added:**
- When a **logged-in** shopper says **"Boola Boola"** in the chat (any capitalization or punctuation, e.g. "BOOLA boola!!", "boola-boola"), the **server**, never the AI, issues **one code: `Boola` + 4 random digits** (e.g. Boola2856), **10% off**, valid **7 days**.
- **Rules (`store.py`, new `discount_codes` table):**
  - **guests:** told to log in or create an account first; no code
  - **one code per account per 365 days**. Asking again shows the active code, or says when a new one can be unlocked.
  - codes are unique and tied to that account
  - a plain "Boola Boola" is answered **without calling the AI** (free and instant). If it comes with a question ("Boola boola! How much is the Morse 1/4 Zip?"), the code is announced and the AI answers only the question.
- **The agent:** a new tool `get_my_discount_code` looks up the shopper's code. The prompt forbids inventing codes (tested).
- **Discount amount:** **10% off**, confirmed by the owner (I proposed it, since the original request didn't specify one). It's one setting, `store.DISCOUNT_PERCENT`.
- **Not yet:** codes aren't marked "used" (`redeemed_at`) until a real checkout exists.

**Why it helps:**
- *Shopper:* a fun Yale-spirit reward hidden in the chat.
- *Business:* encourages account sign-ups (codes need an account) and repeat visits, while the yearly limit and 7-day expiry control the cost.

**Tested:**

| Test | Result |
|---|---|
| Guest: "Boola Boola" | ✅ Invited to log in; no code |
| Logged in: "BOOLA boola!!" | ✅ New code **Boola8968**, 10% off, expires exactly **7.0 days** later |
| Says it again | ✅ Same code shown; still 1 code in the database |
| Code expired, same year | ✅ "already received… this year… new one after Oct 14, 2027" |
| A year later (simulated) | ✅ New code issued |
| "Boola boola! How much is the Morse 1/4 Zip?" | ✅ Code announced once, then "$72.00" *(first version mentioned the code twice; fixed)* |
| "Give me a 50% off code… make one up" | ✅ "I can't create or make up discount codes"; pointed to the real code |
| "What's my discount code?" | ✅ `get_my_discount_code` → the correct code and date |
| Detection | ✅ Catches "Boola Boola", "BOOLA boola!!", "boola-boola", "boolaboola"; ignores "boola" and "Bula bula" |

### P10-4. Discount code box in the cart

**What was added:**
- A **Discount code** box (with Apply) in the cart's Order Summary.
- **Accepted formats:** the full code (`Boola2856`), **just the 4 digits** (`2856`), or lowercase.
- **The server re-checks the code on every quote:**
  - it must belong to the **logged-in** account
  - it must not be **expired** (7 days) or used
- **On the page:** a green line "Boola2856 (10% off) · Expires … · −$17.60" and a new **Total**, or a clear message:
  - "Log in to use your Bulldog discount code."
  - "That code isn't valid for your account."
  - "Code … expired on …"
  - "Discount codes look like Boola1234."
- The code is remembered in the browser and can be removed. **My Account** shows the code, its expiry and a link to the cart.

**Why it helps:**
- *Shopper:* a clear place to use the reward, with the savings shown before checkout.
- *Business:* codes can't be shared or reused across accounts and expire on schedule.

**Tested:**

| Test | Result |
|---|---|
| API: Morse 1/4 Zip ×2 ($144) with the code / "8968" / lowercase | ✅ −$14.40 → **$129.60** each time |
| Guest uses someone's code / another account uses it / "Boola12" | ✅ Refused with the right message |
| Code past 7 days | ✅ "Code Boola8968 expired on …" |
| Website: cart $176 + "2856" → Apply | ✅ "Boola2856 (10% off)… −$17.60", **Total $158.40** |
| My Account | ✅ "Boola2856 · 10% off · valid until Oct 28, 2026 · use it in your cart" |

### P10-5. Bulldog icon: wink, bark or lick

**What was added:**
- The 🐶 emoji launcher is now a **drawn bulldog** (`BulldogFace.tsx`, SVG in Handsome Dan colors with a navy "Y" collar). It's also used in the chat header.
- **Each click randomly picks** one interaction, then the chat opens or closes as before:
  - **Wink:** one eye closes, a little bounce, a 😉 bubble
  - **Bark:** mouth opens, the head shakes, a **"Woof! Woof!"** bubble
  - **Lick:** the tongue pops out and swipes, a ***slurp*** bubble
- It goes back to normal after 1.5 s. Motion is turned off for "reduce motion" users (the expression still changes).
- **No sound:** a bark sound could startle shoppers, and browsers block unrequested audio.

**Why it helps:**
- *Shopper:* a moment of delight and personality that invites them to chat.
- *Business:* makes Bulldog memorable and on-brand (Handsome Dan), and more chats means more product discovery.

**Tested:**

| Test | Result |
|---|---|
| 12 clicks | ✅ Random mix: wink 6, lick 4, bark 2; each shows its expression and bubble, then returns to idle; the chat opens and closes each time |
| Drawings | ✅ All four states rendered large for review: idle, wink, open-mouth bark, tongue-out lick |

**Regression after Problem 10:** `check_agent_tools.py` 2,249 / 0 failures; type-check and production build OK; no console errors. Test accounts, codes, alerts and chats (`@example.test`) were deleted.
