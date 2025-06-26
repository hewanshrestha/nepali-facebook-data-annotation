## Topics

### Politics
- Political parties, coalitions, leadership changes
- Legislation, court rulings, administrative orders, policy debates
- Election campaigning, results, voter behavior
- Excludes cultural/entertainment references to politicians

### Natural Disasters
- Geological: earthquakes, landslides, volcanic eruptions
- Hydrological: floods, tsunamis, glacial lake outbursts
- Meteorological: storms, cold/heat waves, drought
- Space-origin hazards directly impacting Nepal
- Excludes man-made accidents

### Health
- Epidemics/pandemics (dengue, COVID variants)
- Hospital capacity, medical advisories, vaccination campaigns
- Statistics on cases, deaths, recoveries, health studies
- Excludes sports injuries or lifestyle tips unless official

### Sports
- Domestic leagues (cricket, football), player transfers, match results
- Athlete profiles, training camps, sports-governing body announcements
- Excludes metaphorical uses

### Entertainment
- Film releases, song launches, award shows, celebrity birthdays
- Viral memes, fan-made edits of actors/singers
- Excludes political satire with clear policy message

### Education
- Admission notices, scholarship announcements, exam results
- Infrastructure developments, curriculum changes
- Excludes vocational training without institutional affiliation

### Culture
- Local festivals, temple rituals, religious 
- Folk music/dance, craftsmanship, intangible heritage
- Excludes social events lacking cultural significance

### Other
Posts not fitting above categories

## Task 1: Claim Detection

Select **Claim** if the image–text pair contains a verifiable assertion that can be confirmed via external sources and includes at least one of the following elements:

• **Local Context**: References to Nepali entities, events, or administrative units (e.g., "काठमाडौं जिल्ला अदालतले …"). 

• **Who/What/When/Where**: Specific individuals (e.g., "प्रधानमन्त्री"), organizations (e.g., "नेपाल सरकार"), dates, or locations within Nepal (e.g., "पोखरा").

• **Procedures, Laws, Policies**: Citations of Nepali legislation, government orders, or processes (e.g., "नयाँ संविधानको धारा १२३(४) अनुसार …").

• **Numbers and Statistics**: Local figures such as case counts ("९८ नयाँ संक्रमित"), budget amounts ("रू १० करोड"), or turnout numbers ("५० हजारले सहभागिता").

• **Verifiable Predictions**: Forecasts about monsoons, election outcomes, or economic indicators affecting Nepal (e.g., "यस वर्ष हिमाली क्षेत्रका २० गाउँ डुबानको जोखिममा छन्").

• **Image References**: Claims about the content of the image, especially when depicting Nepali contexts (e.g., "यो तस्बिरले बाढी प्रभावित क्षेत्र देखाउँछ").

• **Code-Mixed Expressions**: Assertions blending Nepali (Devanagari) and English (Roman script) must be treated as claims if they include verifiable content (e.g., "Nepal's GDP growth ५% छ").

• **Text Overlays & Memes**: Claims embedded in image text overlays or memes (e.g., a meme stating "बेरोजगारी दर २०% पुगेको छ").

Label as **No Claim** if none of the above criteria are met or the text is purely opinion, anecdote, or greeting without verifiable content.


## Task 2: Checkworthiness Detection

For items labeled Claim in Task 1, select **Check-worthy** if the claim exhibits one or more of the following properties—tailored to high-impact Nepali Facebook content:

• **Harmful or Defamatory Content**: Attacks or rumors against individuals, parties, ethnic groups, or communities (e.g., "जनजाति विरोधी टिप्पणी") that can incite social discord.

• **Urgent/Breaking News**: Statements about active crises, protests, disasters, or policy shifts (e.g., "नेपाल बन्दको तयारी", "बाढीले १०० गाउँ डुबाइदियो").

• **Public-Interest Value**: Claims affecting large populations—health alerts, educational reforms, constitutional amendments (e.g., "नयाँ चुनाव मितिलाई १५ दिनले स्थगित गरियो").

• **Recent-Law & Official Rulings**: References to newly enacted laws, Supreme Court decisions, treaties influencing Nepali citizens (e.g., "नयाँ व्यापार समझौता अनुच्छेद ७ बमोजिम…" ).

• **Visual Sensationalism & Mismatch**: Dramatic images (collapsed bridges, riots) paired with urgent text or when image content contradicts text claims.

• **Emotive or Panic-Inducing Language**: Posts evoking fear or outrage (e.g., "नेपालमा चिप निलम्बन हुने अफवाह फैलियो").

• **Conspiracy/Scandal Indicators**: Unverified plots or scandals (e.g., "shadow government" claims about Nepalese politics).

• **Repost or Source Alerts**: Mentions of viral chains or second-hand sources (e.g., "WhatsApp मा भाइरल") that require origin tracing.

Label as **Not Check-worthy** if the claim lacks these high-impact or urgency cues despite being verifiable.


## Need Help?
If you have any questions or need clarification, please contact the project administrator. 