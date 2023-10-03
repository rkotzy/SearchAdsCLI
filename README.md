<h1 align="center">SearchAdsCLI</h1>

SearchAdsCLI is a command line interface for setting up Apple Search Ads campaigns and does the heavy lifting around adding new keywords in a three campaign structure.

# Quickstart

1. Set up Apple Search Ads account create an API user
2. pip install searchads
3. searchads configure
4. searchads setup-campaigns
5. searchads add-keywords
6. Profit 🎉

# Generate Search Ads API Key

1. Account administrators invite users with API permissions using the following process:
    1. From the [Apple Search Ads UI](https://searchads.apple.com/), choose Sign In > Advanced and log in as an account administrator.
    2. From the Users menu in the top-right corner, select the account to invite users to.
    3. Choose Account Settings > User Management.
    4. Click Invite Users to invite users to your Apple Search Ads organization.
    5. In the User Details section, enter the user’s first name, last name, and Apple ID. Note that you may need to create a secondary Apple account, as the Apple Search Ads owner cannot be an API user as well.
    6. In the User Access and Role section, select an API user role.
    7. Click Send Invite. The invited user receives an email with a secure code. The user signs into the secure Apple URL in the email and inputs the provided code, which activates the user’s account.

2. Generate Private Key: 

```bash
openssl ecparam -genkey -name prime256v1 -noout -out private-key.pem
```

3. Generate Public Key:

```bash
openssl ec -in private-key.pem -pubout -out public-key.pem
```

4. Open the `public-key.pem` file in a text editor and copy/paste the public key, including the begin and end lines, into the Apple Search Ads dashboard.

# Installation

```bash
pip install searchads
```

# Configure

First, you’ll need to provide some configuration details so SearchAdsCLI can communicate with your Apple Search Ads account. Run `searchads config` and follow the prompts.

```bash
searchads config
```

# Create Campaigns
Creating campaigns through SearchAdsCLI creates a three campaign structure automatically.

1. **Exact Campaign:** This is your core campaign that bids on exact matches to provided keywords.
2. **Discovery Campaign:** This is an exploratory campaign that bids on similar keywords to those in your Exact Campaign, but explicitly blocks the identical keywords to avoid bidding against yourself between campaigns. The goal of the Discovery Campaign is to uncover new keywords to feed into the Exact Campaign.
3. **Competitor Campaign:** This campaign is setup the same as the Exact Campaign, with bids on exact matches to provided keywords, but it specifically designed for competitor app names. The reason for making this a separate campaign is to have control over the daily spend. Generally you’ll spend less per day on the Competitor Campaign then you would on the Exact Campaign.

This campaign structure is widely used, and even recommended by Apple ([ref](https://searchads.apple.com/best-practices/campaign-structure)).

To begin creating campaigns, run the following command:

```bash
searchads setup-campaigns
```

## Choose countries

You’ll be prompted to enter the country or countries you want the campaigns to run it. The default is the United States. You may want to use a list of countries if you want to run campaigns in a region of similar, smaller countries. If you're just starting out, stick to a single Tier 1 country.

## Pause existing campaigns
Next, the CLI will search for any active campaigns already running in the selected countries. If any are found, you’ll be asked if you want to pause those active campaigns. It’s recommended that you pause any campaigns already running so they don’t compete with any newly created campaigns.

## Enter daily budgets

You’ll need to enter a daily budget for each campaign being created. It’s not guaranteed your entire budget will be spent each day, but you won’t spend more than the limit. Think of it as an approximate maximum spend.

**Discovery campaign**

A good practice is to allocate 20% of your budget to the Discovery campaign.

**Exact campaign**

This should be the majority of your budget.

**Competitor**

Your budget here will vary based on the direct competition you’re targeting. 

## Enter default bid

In addition to the daily budget, you need to enter a default bid for each keyword created under the campaigns. Typically this is in the range of $0.50 - $2.00 USD but can (and should) be adjusted on a keyword-by-keyword basis later to optimize your campaigns. 

## Campaigns created!

With country and budget information entered, your campaigns will automatically get created in your Apple Search Ads dashboard. You should be able to see the newly created campaigns there with a `SearchAdsCLI_` prefix in the name.

> 🚧 Do not change the name of any Campaigns or Ad Groups created by SearchAdsCLI from the Apple Search Ads dashboard!

# Add Keywords
After creating your campaigns, it’s a good idea to add some initial keywords. When adding keywords through SearchAdsCLI they’ll be created in two places:

1. Keywords will be added to your Exact Campaign to bid against exact matches for the word.
2. Keywords will be added to your Discovery Campaign as broad match keywords. This will allow the campaign to discover similar keywords.

To add keywords, run:

```bash
searchads add-keywords
```

You’ll be prompted to select which campaign you want to create the keywords in. This is useful if you’re running campaigns in different countries or regions and only want to add a keyword for a specific country/region.

## Competitor keywords

If you want to add competitor names to your Competitor Campaign, run the `add-keywords` command with a `competitor` parameter.

```bash
searchads add-keywords --type competitor
```

This will add exact matches for the word in your Competitor Campaign but will NOT add a broad match for the term in your Discovery Campaign.

## Negative Keywords

If there are keywords you want to prevent from ever bidding against, you can add these as negative keywords through SearchAdsCLI. Adding a negative keyword will prevent any of your campaigns from bidding against these keywords unless added back through `add-keywords`.

# Campaign management

Your campaigns are up and running - now what? First and foremost, patience is key. Allow at least 24 hours after setting up a new campaign to check on results. This will give time to gather enough data to display any meaningful results.

## 1. Leverage the Discovery Campaign

- **New Keyword Ideas:** Regularly review the keywords from your Discovery Campaign. This campaign is designed to help you discover potential new keywords that are relevant to your app.
    - **Adding Keywords:** If you find a new keyword from your Discovery Campaign that leads to a successful app installation, you should move it to your Exact Campaign. Use the command **`searchads add-keywords`** to add it.

## 2. Optimize Your Keyword Bids

- **Adjust Bids:** Make a routine to adjust your keyword bids (CPT) daily based on the performance.
    - **Low Impressions:** If your keywords are not getting enough impressions, consider increasing your bids. A higher bid can improve the visibility of your ad in search results.
    - **Low Conversion:** On the contrary, if you're seeing high impressions but they're not translating to conversions, consider lowering the bids. This will help manage your budget more effectively.

## 3. Understand the Lifetime Value (LTV)

- **Evaluate LTV:** After the first few weeks of running campaigns, dedicate time to understanding the Lifetime Value (LTV) of users acquired through ads.
    - **Compare LTV:** For some keywords, the LTV from users who install via the ads may be higher than those who come organically, while for others, it might be the opposite. Identifying these patterns can help you allocate your budget to the most profitable keywords and help you set CPT benchmarks.

**Feedback?** If there’s something else you’d like to see covered here open an issue or submit a PR.
