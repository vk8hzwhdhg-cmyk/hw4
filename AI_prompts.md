# AI Prompts — Homework 4

This file records the prompts I gave the AI assistant for Homework 4, in order. Each problem must include its number and title, at least one prompt I typed, any follow-up prompts, and one sentence explaining what the first prompt lacked or how it could be improved. Code and JSON outputs serve as evidence of completed work. API keys and other secret values must never be recorded here.

## Problem 1: Project setup and prompt log — Prompt 1

Hey there, we're going to be working on Homework Number 4 for my AI Foundations for Managers Class. Today we're going to build a campus customs Web site with a helpful chatbot. We're going to be using React + Vite TypeScript front end and a Python FastAPI backend whose brain is a Pydantic AI agent. As an output, shoppers should be able to browse products, create an account, chat about merch, see matching items appear on the page, and get honest answers about price and stock from a local database. In the Homework 4 folders, you should see some files in a data folder. The campus_customers.db has tables for the product catalog, inventory by size, and users. Product image file paths are there too. For style, your guide is yalebulldogblue.com for the design aesthetic for the Campus Customs page and information for the agent prompt. In the end, we'll push the project to a public GitHub repo. Do NOT commit the database or production images.

We're going to work one problem at a time. Each problem must include its number and title, at least one prompt I typed, any follow-up prompts, and one sentence explaining what the first prompt lacked or how it could be improved. Code and JSON outputs serve as evidence of completed work. API keys and other secret values must never be recorded here. To record the prompts, please create an AI_prompts.md file. All good?

**How to improve the initial prompt:** The database filename was off (the actual file is `campus_customs.db`, not `campus_customers.db`), and the prompt didn't say which model provider/API key to use or where the project root should live.

## Problem 2: Analyze the database and start the harness — Prompt 1

Please rename the first prompt under problem 1. We're now moving on to problem 2. We are going to analyze the database data/campus_customs.db and ensure that we understand the fields of each table. Just checking in to ensure that you get the catalouge, inventory, and users, fields (and any others). Also, please create the file output/harness.md where you will wirte down each table and its fields and one short line on why each field matters for the shop or the chatbot, we'll continue to add to this harness later

**How to improve the initial prompt:** It could have asked for data-quality checks up front (e.g. orphaned inventory rows, sold-out counts, JSON-encoded text columns, inconsistent garment types), and it combined a housekeeping edit to Problem 1 with the new Problem 2 task.

**Evidence:** `output/harness.md`

## Problem 2: Analyze the database and start the harness — Prompt 2 (follow-up)

Can you check for any quality or other issues in the tables and flag them if there are any?

**Evidence:** "Data-quality audit — flagged issues" section in `output/harness.md`

## Problem 2: Analyze the database and start the harness — Prompt 3 (follow-up)

can you create a second, cleaned database? I want to keep the original intact in case it's needed latere in the homework sets but I'd also like to try and resolve the issues ahead of time as well

**Evidence:** `scripts/clean_db.py`, `output/cleaning_report.json`, "Cleaned database" section in `output/harness.md` (the cleaned `.db` file itself is not committed)

## Problem 3: Scaffold the React + Vite front end and FastAPI product API — Prompt 1

Onto problem 3. Let's scaffold a React + Vite + TypeScript front end for Campus Customs, put a nav bar at the top that links to the main pages in the bullets below. Please use the Campus Customs-style wording from our reference at yalebulldogblue.com. For Home and About Us, I've added my own wording; please use that.

* Home - Bring Tradition with you with you wherever you go. Official Yale Merch.
* Products
* About Us - Family-owned and operated for over 50 years. We're part of the Yale fabric and produce on site for quick turnarounds while supporting the local community. We've got you covered for all of your Yale merch needs. Reach out if you have any questions or would like to create a Campus Custom idea with us.
* Log In
* Create Account

For the products pages, show product images from the catalogue (use database image paths) along with product information, name, price, short description. Each product should open a single-tem page, using a common format seen on retail websites. A large image on one side, product infomation on the other (text, sizes/stock if avalaible) clicking on a card on the products page should take the shopper there. Also, let's add a Bulldog chat bot on the bottom right, it doesn't need to talk yet, we'll work on that in a bit. We'll need prep a small API to read the database, a simple FastAPI app in backend/main.py to serve products and images and we'll grow the agent backend later.

**How to improve the initial prompt:** It didn't say which database to use (original or cleaned), whether Log In / Create Account should work yet or just be forms, or whether the Products page needs filtering/search; and the Home tagline had a duplicated "with you".

**Evidence:** `backend/main.py`, `frontend/src/` (pages, components, `api.ts`), "App architecture" section in `output/harness.md`

## Problem 3: Scaffold the React + Vite front end and FastAPI product API — Prompt 2 (follow-up)

One additional thing. I believe we didn't set up the PORTKEY_API_KEY in a .env file. Can you pull it from the previous homework and put here for future use, I assume we'll need to be calling AI later on. Please use the Sol 5.6 model.

Obviously, please ensure that the PORTKEY_API_KEY is never shared publicly.

**Evidence:** `.env.example` (placeholders only), "AI configuration" section in `output/harness.md`. The real key lives only in the git-ignored `.env` and is not recorded here.

## Problem 4: Create account and login workflow — Prompt 1

On to Problem 4. We're going to create a normal create account & login workflow. It should have

* Create Account: first name, last name, email, password (confirm password)

* Log In: email and password

**How to improve the initial prompt:** It didn't define what "normal" means for security and behavior: how passwords should be hashed, how long a login should last, where to send the shopper after signing up, what the nav should show when logged in, or how to handle the 3 existing accounts whose hash format doesn't record its settings.

**Evidence:** `backend/auth.py`, `backend/main.py` (auth router + safe validation errors), `frontend/src/AuthContext.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/pages/CreateAccount.tsx`, `frontend/src/components/NavBar.tsx`, "Accounts and login" section in `output/harness.md`

## Problem 4: Create account and login workflow — Prompt 2 (follow-up)

There should be a test user in the database, test@campustcustoms.yale.edu. Can you use that to test the login? Also, please update the output/harness.md with how authorizations works, what you store for a user and how passwords are protected.

**Evidence:** "Accounts and login" section in `output/harness.md` (subsections: How authorization works, What we store for a user, How passwords are protected). Test User exists as `test@campuscustoms.yale.edu` (my prompt had a typo, "campustcustoms").

## Problem 4: Create account and login workflow — Prompt 3 (follow-up)

I'd like to test the login function

## Problem 4: Create account and login workflow — Prompt 4 (follow-up)

The new account works, but the test user did not.

## Problem 4: Create account and login workflow — Prompt 5 (follow-up)

The Test User login worked this time.

**Evidence:** `backend/auth.py` (`_verify_legacy` tries common PBKDF2 settings for the original accounts; the confirmed setting, 120,000 iterations with a text salt, is now the default). The server log recorded only the matched setting, never the password. Test User's hash was upgraded to the 600,000-iteration format on login. No passwords are recorded in this file.

## Problem 4: Create account and login workflow — Prompt 6 (follow-up)

Great. Please also log how the correct authentication works (and how the user, and passwords are protected, and how) in the output/harness.md

**Evidence:** "Accounts and login (Problem 4) — verified reference" section in `output/harness.md`, covering the step-by-step authentication flows, authorization and stored data, password protections, and the verification log.

## Problem 5: Build the shop chatbot (Pydantic AI agent behind FastAPI) — Prompt 1

We're onto problem 5, building the shop chatbot. We're going to do that as a pydanticAI agent behind FastAPI, plugged into the fornt-end chat widget. Please put the API app in backend/main.py which will be the file you run with Uvicorn. We're going to keep the agent as four files, backend/prompts/prompt.md - system prompt
backend/agent.py - agent entry / wiring
backend/tools.py - tools the agent can call
backend/models.py - pydantic / pydanticAI structured types
In main.py expose a chat route so a message from the Web site returns a reply from the agent, you will be using the API key for the agent. Place Campus Customs voice and safety basics into prompts/prompt.md, which we will update later. Start or update types in models.py for chat replies and product cards as needed. In output/harness.md note now the frond end talks to FastAPI and how the agent is loaded (prompt file + model). Please make sure the backend runs from the backend/folder like this - uvicorn main:app --reload --port 8000

**How to improve the initial prompt:** It didn't say whether chat history should be saved to the `chat_messages` table for logged-in shoppers or kept in the browser, which tools the agent should have (search, stock by size, categories), or how the bot should handle requests outside the shop's scope, such as discounts or return policies.

## Problem 5: Build the shop chatbot — Prompt 2 (follow-up)

why did it pause?

## Problem 5: Build the shop chatbot — Prompt 3 (follow-up)

keep going with problem 5

**Evidence:** `backend/main.py` (`POST /api/chat`), `backend/agent.py`, `backend/tools.py`, `backend/models.py`, `backend/prompts/prompt.md`, `frontend/src/components/ChatWidget.tsx`, "Shop chatbot (Problem 5)" section in `output/harness.md` (architecture, agent loading, and live test results). The API key stays in the git-ignored `.env` and is not recorded here.

## Problem 5: Build the shop chatbot — Prompt 4 (follow-up)

For the hoodie price can you show me where you are seeing the two numbers

## Problem 5: Build the shop chatbot — Prompt 5 (follow-up)

Can you show me the original?

## Problem 5: Build the shop chatbot — Prompt 6 (follow-up)

I think we should keep the original price from the database. While I understand the logic of line pricing the item, we don't know the reason for the price variation, let's not invent pricing, we should stick to the original price.

**Evidence:** `scripts/clean_db.py` (`ROW_FIXES` no longer changes the price), `output/cleaning_report.json` (136 changes; `owner_decisions` records the decision), "Cleaned database" section in `output/harness.md` (new rule: cleaning never changes prices). The tennis hoodie is $45 in the cleaned database, the product API, and Bulldog's replies. The fix was applied in place, so app accounts were kept, and a rebuild on a scratch copy also produced $45.

## Problem 6: Database lookup tools for the agent — Prompt 1

Onto problem 6. We're going to supply the agent with tools that look up the real information from campus_customs.db. You may have done some of this already. You must use the database; again, don't invent prices or quantities. If out of stock, say so clearly. Be sure you can read the below from the database.

* Product description
* Price
* How many are in stock (by size when the customer asks)

Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In the output/harness.md list each tool and explain which model fields you choose for lookup results and why.

**How to improve the initial prompt:** It named `campus_customs.db`, but the app reads the cleaned copy, so it could have said which database the tools should use (or asked for proof the two match). It also didn't say whether the bot should give exact stock counts or just "in stock / low / sold out", or how to handle products and sizes that don't exist.

**Evidence:** `backend/tools.py` (`search_products`, `get_product_details`, `get_price`, `check_stock`, `get_categories`), `backend/models.py` (`ProductMatch`, `ProductInfo`, `PriceInfo`, `StockCheck`, `NotFound`), `backend/prompts/prompt.md` (tool table and price/stock answer rules), `scripts/check_agent_tools.py` (2,249 checks vs `campus_customs.db`, 0 failures), "Agent lookup tools (Problem 6)" section in `output/harness.md` with live test results.

## Problem 7: Dynamic product cards from the agent — Prompt 1

We're going to build on that work with Problem 7. The Web site should dynamically show the matching items as product cards (image, name, price, short info) when asked a question like, what hoodies do you have? This should be like an API contract where the agent returns structured product match and the frond ent renders them on the website. After the dynamic product cards are loaded by the new feature, make sure that the same single-item page behavior from Problem 3 still works, each product card (even ones in the chat) should still open the detail view. Update prompts/prompt.md and output/harness.md

**How to improve the initial prompt:** It didn't say *where* on the website the cards should appear (a section on the current page, the Products page, or only in the chat), how many cards to show when many items match (27 hoodies), or what should happen to the cards when the shopper opens a product or asks a new question.

**Evidence:** `backend/models.py` (`AgentReply.product_ids` + `results_title`, `ChatResponse`, `ProductCard`, `SearchResults`), `backend/agent.py` and `backend/tools.py` (server builds cards from the DB), `frontend/src/components/ChatResults.tsx`, `ChatResultsContext.tsx`, `ProductCard.tsx`, `ChatWidget.tsx`, `backend/prompts/prompt.md` ("Showing products on the page"), "Dynamic product cards (Problem 7)" section in `output/harness.md` with the API contract and test results.

## Problem 8: Chat memory, customer context and page context — Prompt 1

Onto problem 8. We'll add memory to the customer chat history. When a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name and email). Put it in a clear pattern, like agent deps and/or tools the agent can call. Pass enough page context that if someone is on a product page and asks, "Do you have this in pink?", the agent knows which item they mean. You can put code into the agent context if necessary. History only needs to persist for logged-in users. Documents in output/harness.md, how the chat history is stored, what customer fields the agent sees, and how page context is passed.

**How to improve the initial prompt:** It didn't say how much history the agent should see, whether shoppers should be able to delete their saved chat, or whether sending the shopper's email to the model provider is acceptable. It also didn't say what to do with the 22 existing course messages in `chat_messages`.

**Evidence:** `backend/memory.py`, `backend/models.py` (`PageContext`, `Shopper`, `CurrentPage`, `ShopDeps`, `PageInfo`, `AccountInfo`, `HistoryMessage`), `backend/tools.py` (`resolve_page`, `get_current_page`, `get_my_account`), `backend/agent.py` (dynamic instructions, history from the DB, saving), `backend/main.py` (`GET`/`DELETE /api/chat/history`), `frontend/src/components/ChatWidget.tsx`, `backend/prompts/prompt.md` ("Who you're talking to and where they are"), "Chat memory… (Problem 8)" section in `output/harness.md` with test results.

## Problem 8: Chat memory, customer context and page context — Prompt 2 (follow-up)

I like the suggestions of allowing the guest to be able to clear their chat history. Let's assume you keep a 30 days chat history and after that it is cleaned, unless the user decides to clear it before that time. Let's offer a button to clear, it can be a subtle button opposite the send button to ensure they don't hit it by accident.

**Evidence:** `backend/memory.py` (`RETENTION_DAYS = 30`, `purge_expired`, 30-day read filter), `backend/main.py` (purge on startup via `lifespan`), `frontend/src/components/ChatWidget.tsx` (Clear opposite Send, with confirmation, for guests and logged-in shoppers), `backend/prompts/prompt.md` (retention answer), "Retention and clearing" section in `output/harness.md`. Note: the 30-day rule removed the 22 original course chat messages from the cleaned database; they remain in the original `campus_customs.db`.

## Problem 8: Chat memory, customer context and page context — Prompt 3 (follow-up)

You can keep the test since that we're using that to learn. We want to save the logged in guests chat history for up to 30 days, unless they clear the chat history and the the clock begins again.

**Evidence:** `backend/memory.py` (per-shopper 30-day clock, `purge_expired`, `is_sample` exemption, `ensure_schema`), `scripts/clean_db.py` (marks the 22 course messages as samples), `backend/prompts/prompt.md` (updated retention answer), updated "Retention and clearing" section in `output/harness.md`. The 22 course messages were restored from the original `campus_customs.db` and are kept as sample data.

## Problem 9: Usability improvements — Prompt 1

Alrighty. Problem 9. We're going to add some usability improvements. We've already started doing this in the last prompt of problem 8. Our aim is to add 2 front-end usability improvements and 2 agent / backend usability improvements. Let's count the clear chat as one backend usability improvement. Write output/usability.md before you build as and add to it as you build. For each improvement, say 1) what was added and 2) why it helps a campus customs shopper or the business. After you add the improvements, please test them. For the additional backend improvement, please add a security backend for the customer, you mentioned something about sharing customer info via the api key before, how can we better secure customer data?

**How to improve the initial prompt:** It could have named the two front-end improvements (or the shopper problems they should solve) and said how much customer data the agent still needs after Problem 8. For example: "first name is enough, keep the email on the server."

**Evidence:** `output/usability.md` (written before building, then updated with each improvement and its tests), `backend/privacy.py`, `backend/agent.py`, `backend/tools.py`, `backend/auth.py`, `backend/models.py`, `frontend/src/components/ChatWidget.tsx`, `frontend/src/pages/ProductPage.tsx`, `frontend/src/chatEvents.ts`, `frontend/src/index.css`, "Usability and security improvements (Problem 9)" section in `output/harness.md`.

## Problem 9: Usability improvements — Prompt 2 (follow-up)

It seems you went ahead and added some front end items. I'd like to have a look and check for my own. Can you bring it up here so I can have a look and make suggestions please?

## Problem 9: Usability improvements — Prompt 3 (follow-up)

A couple of quick questions. Are there male/female options for these items?

## Problem 9: Usability improvements — Prompt 4 (follow-up)

For some additional front-end things to add, 1) please put additional filters for sports, schools, colleges, and relatives in the shop all products page where there are the other filters like hoodies, etc. listed. 2) please add a map under Come visit us! in the about us page. Please give the option for the user to open that map in Google Maps or Apple Maps, or their choice. Some other small tweaks, in the chat change the "Saved to your account for 30 days" to "Chat auto saved to your account for 30 days" for the "Clear" button change to "Clear Chat"

**Evidence:** `backend/tools.py` (`COLLECTIONS`, `list_collections`, `collection` filter), `backend/main.py` (`GET /api/collections`), `frontend/src/pages/Products.tsx` ("Shop by" row), `frontend/src/pages/About.tsx` (map + open-in-app links), `frontend/src/components/ChatWidget.tsx` (new wording), F3/F4 sections in `output/usability.md`.

## Problem 9: Usability improvements — Prompt 5 (follow-up)

The map shows correctly on the About page in my browser.

## Problem 9: Usability improvements — Prompt 6 (follow-up)

Do you recommend any other improvements?

## Problem 9: Usability improvements — Prompt 7 (follow-up)

Let's add these.

4. Add to Cart does nothing. The button lights up but there's no cart or checkout. Either build a simple cart, or relabel it so it doesn't promise something we don't do. - Add the cart, silly oversight on my side.
5. Rate limit the chat. Anyone could send thousands of messages and run up the Portkey bill. A per-visitor limit (e.g. 20 messages per minute) protects the budget. - Fair point, let's change it to 20 messages per minute, with a cap of 200 messages saved.
6. Fit and sizing info. You asked about men's/women's. Bulldog can only say "XS–XXL, two are labeled men's". A size guide (or a fit field the owner fills in) would answer the most common pre-purchase question. - If you can find a size guide to add please do, we'll use it in place of a real one for a real website.
7. Sort and price filter on Products (price low→high, in stock only). It's small, and shoppers expect it. - Add
8. "Notify me when back in stock." Bulldog currently says "I can't send restock texts". Saving an email per sold-out size is a direct sales recovery. - Add
9. A simple account page (name, email, chat history, sign out). Bulldog has to avoid pointing shoppers to one because it doesn't exist yet. - Add

Once those are added. run the checks that are needed for the github push

**Evidence:** `backend/store.py`, `backend/size_guide.json`, `backend/main.py` (cart, size guide, restock, account routes; chat rate limit), `backend/memory.py` (200 cap), `backend/models.py`, `backend/prompts/prompt.md`, `frontend/src/CartContext.tsx`, `pages/Cart.tsx`, `pages/Account.tsx`, `components/SizeGuide.tsx`, `components/NotifyMe.tsx`, `pages/Products.tsx`, `pages/ProductPage.tsx`, "Shop features round" in `output/usability.md` and `output/harness.md`, plus the pre-push check results.

**Pre-push check results:** see "GitHub pre-push checks" in `output/harness.md`. No secrets or personal data are in the files to be committed. One fix was made: a clear setup error plus `data/README.md` for clones that don't have the data. One item is open: the root README.

## Problem 9: Usability improvements — Prompt 8 (follow-up)

Not yet, I'll decide on the README later.

## Problem 9: Usability improvements — Prompt 9 (follow-up)

You can put the recent usability changes in the usability.md

**Evidence:** `output/usability.md`. Summary table now lists B1–B2, F1–F4, S1–S7 and the wording tweaks. New S7 section covers the fresh-clone setup fix, and B1 cross-references the 200-message cap.

## Problem 10: Style the website (look & feel, hero video, Boola Boola code, Bulldog interactions) — Prompt 1

Onto problem 10. Style up the website. You've done a great job so far making it look like a campus customs storefront. Let's continue to upgrate the look and feel. 1) ensure the fonts/typeface, color, and general look are similar to the actual Web site. 2) on the home page, instead of the plain blue top portions of the website, can you add a 5-8 second lifestyle video of students wearing the merch around campus? Then move into a static image of students wearing the merch, only play the video when someone goes onto the page, don't replay and use the static image after the video. 3) if someone in the chat says "Boola Boola" caps/lowercase does not matter, they get a one time discount code for the merch. Only provide one per logged-in user (no guests), one time per year. The discount code can be Boola####. 4) Add a place to input the number randomly generated for that logged-in user. Let the code have a shelf life of 7 days. 5) If you click the bulldog icon it interacts with you by winking, barking, or licking. Randomly choose which interaction each time.

**How to improve the initial prompt:** It didn't say how big the discount should be (I chose 10%), where the lifestyle video should come from (I used the Homework 3 Campus Customs ad, muted), whether "don't replay" means per visit or per session (I chose per browser session), or whether a code should be marked as used at checkout.

**Evidence:** `frontend/src/index.css` (Problem 10 theme), `frontend/src/components/HeroVideo.tsx`, `frontend/public/hero/README.md`, `backend/store.py` (Boola codes, `_apply_code`), `backend/agent.py`, `frontend/src/pages/Cart.tsx`, `frontend/src/pages/Account.tsx`, `frontend/src/components/BulldogFace.tsx`, `frontend/src/components/ChatWidget.tsx`, `backend/prompts/prompt.md`, "Problem 10" sections in `output/usability.md` and `output/harness.md`.

## Problem 10: Style the website — Prompt 2 (follow-up)

Keep the Boola Boola discount at 10%.

## Problem 10: Style the website — Prompt 3 (follow-up)

I see you used the video from before. Can you create  a new one? More in line with my request for yale student life. This is under a highway, and doesn't reflect the lifestyle image of yale

**Result so far:** I tried to generate a new Yale campus-life clip with **Sora 2** through Portkey (models `sora-2`, `sora-2-2025-12-08`, `sora-2-2025-10-06`, `aoai-sora`, `sora`), and AI stills with `gpt-image-1/1.5/2`. All were rejected: the course Portkey key routes every request to one Azure text deployment (`gpt-5.6-luna`), so video and image generation aren't available on it. No content was generated and nothing was charged. A search found no free, reusable Yale footage showing the merch. Options were given to the owner; the hero is unchanged for now.

## Problem 10: Style the website — Prompt 4 (follow-up)

Okay, let's skip the video, can you create a static image of a lifestyle campus scene with students wearing some of the merch in the catalouge?

**Evidence:** `frontend/public/hero/campus-scene.svg` (original illustration: Gothic campus at golden hour; students in Basic Hoodie Big Yale, Yale Sports Hoodie Tennis, Champion Reverse Weave Crewneck and Baseball Left Chest Crewneck), `frontend/src/components/HeroImage.tsx`, `frontend/public/hero/README.md`, updated P10-2 in `output/usability.md`. The video files were removed.

## Problem 10: Style the website — Prompt 5 (follow-up)

I guess beauty is in the eye of the beholder. I am looking for something more like this from the original page. Are you able to generate imagery like this?

*(Attached: the hero banner from yalebulldogblue.com, showing students in Yale tees and sweatshirts with the "YALE BULLDOG BLUE / Officially Licensed Merchandise" logo.)*

## Problem 10: Style the website — Prompt 6 (follow-up)

Yes, use the banner I attached as the home page hero, kept out of GitHub like the product photos.

**Evidence:** `frontend/src/components/HeroImage.tsx` (banner shown whole with the headline band below; falls back to the illustration if the banner is missing), `.gitignore` (`frontend/public/hero/yale-bulldog-blue-banner.*`), `frontend/public/hero/README.md`, updated P10-2 in `output/usability.md`. I couldn't generate photo-realistic imagery myself: the course Portkey key blocks image and video models, and code-drawn vectors can't look photographic.

## Problem 10: Style the website — Prompt 7 (follow-up)

If the banner is missing, default to the navy blue background from before, not your generated image.

## Problem 10: Style the website — Prompt 8 (follow-up)

resume, i hit cancel by accident

**Evidence:** `frontend/src/components/HeroImage.tsx` (fallback is now the original navy `.hero`), `campus-scene.svg` deleted, `frontend/public/hero/README.md`, updated P10-2 in `output/usability.md`. Tested by hiding the banner (navy hero shown), then restoring it (banner shown).

## Problem 10: Style the website — Prompt 9 (follow-up)

Write the changes in output/design.md, record what changes and why it should keep customers around and buy. Keep it short.

**Evidence:** `output/design.md`

## Problem 11: Site testing and app check — Prompt 1

Let's move to problem 11. Site testing and app check. Test the live site and document it int output/app_check.html. Include clear screenshots and short captions for: 1) chat checking the inventory level of an item; 2) the dynamic search result cards appearing after a question; 3) one of the usability features we added in problem 9. Make the HTML easy to grade: a heading for each check, a screenshot, and 1-2 sentences on what the screenshot proves. Put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths.

**How to improve the initial prompt:** It could have said which Problem 9 feature to show (I chose "Ask Bulldog about this item"), whether to test as a guest or a logged-in shopper, and at what screen size (I used a guest at 1100×760 desktop).

**Evidence:** `output/app_check.html` and 5 screenshots in `output/app_check_images/` (01 inventory check; 02a/02b dynamic cards; 03a/03b Ask Bulldog). All three checks pass and match `campus_customs.db`.

## Problem 12: Audit trail, safety, finish harness — Prompt 1

Problem 12. Audit trail, safety, finish harness. Let's keep an append-only output/audit_trail.json of the agent loop activity (time, tool name, short args/result, stop reason). Do not wipe between runs. Please suggest any additional safety measures we should add.

**How to improve the initial prompt:** It didn't say whether the audit trail should be committed to GitHub (it contains user IDs and short redacted message previews), how long it should be kept, or whether non-AI outcomes (rate limits, provider blocks, the Boola shortcut) should be logged too. I included them.

**Evidence:** `backend/audit.py`, `backend/agent.py` and `backend/main.py` (audit hooks), `output/audit_trail.json` (25 entries from test turns; survived a server restart unchanged), "Audit trail (Problem 12)", "Safety summary (final)" and "Recommended next safety measures" in `output/harness.md`.

## Problem 12: Audit trail, safety, finish harness — Prompt 2 (follow-up)

Should that be committed?

## Problem 12: Audit trail, safety, finish harness — Prompt 3 (follow-up)

If it's on github and someone decides to go crazy testing the chat, what happens?

## Problem 12: Audit trail, safety, finish harness — Prompt 4 (follow-up)

We're not going public so that's okay. Let's finish the output/harness.md. Ensuring it's clear how the system works. Model fields in models/py and why you chose them, tools and abilities, safety rules, specs (loop limits, results caps, models, how to run front & back)

**Evidence:** `output/harness.md` Part 1 "Start here: how the system works", covering (1) what it is with an architecture diagram, (2) how to run the front and back end, (3) specs (model, framework, **agent loop limits**, result caps, rate limits, retention, accounts, cart, discount), (4) every `models.py` model with its fields and why, (5) the 10 tools and abilities, (6) safety rules in the prompt and enforced in code. The build log was kept as Part 2. New: explicit loop limits `UsageLimits(request_limit=8, tool_calls_limit=12, total_tokens_limit=80_000)` in `backend/agent.py`, with a friendly reply and `stop_reason: usage_limit` in the audit trail when one is hit (tested). Every model, tool and number in Part 1 was checked against the code.

## Problem 13: Final layout check before the GitHub push — Prompt 1

Problem 13. We're going to put the code in a folder named hw4 and push it to a public GitHub repository. We'll then submit the repo URL to the graders. Before we do that, can you ensure we're not missing any items? The expected file layout is attached. The agent should be four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. README.md should explain how to run the front end and back end after placing the data pack.

*(Attached: the expected `hw4/` layout, plus the local-only data pack `data/campus_customs.db` + `data/products/`.)*

**How to improve the initial prompt:** It could have said whether supporting backend files (auth, memory, store, privacy, audit) are allowed alongside the five listed files, and whether "hw4" means renaming the local folder or only the repository.

**Evidence:**
- **Fixes:** new root `README.md`; `requirements.txt` moved to the root; all 10 agent tools moved into `backend/tools.py` (3 were in `store.py`); the backend now builds the cleaned DB automatically from the data pack on first start; removed `data/README.md` and the Vite template `frontend/README.md`.
- **Fresh-copy test following only the README:** installed and ran, built the DB, served 102 products, chat answer matched the DB, 2,249 checks / 0 failures, build passes. The test copy was deleted afterwards.

## Problem 13: Final layout check before the GitHub push — Prompt 2 (follow-up)

Keep the local folder name; just name the GitHub repository hw4.

## Problem 13: Final layout check before the GitHub push — Prompt 3 (follow-up)

Yes, commit and push to a new public GitHub repo named hw4 under vk8hzwhdhg-cmyk, with my Yale email as the author.

**Evidence:** public repository `vk8hzwhdhg-cmyk/hw4` (66 files). The pre-push scan found no API key, password hashes, test passwords, user emails, databases, product images or banner in the committed files.
