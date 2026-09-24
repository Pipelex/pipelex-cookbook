# Key: discord_week

Inputs: `discord_channel_updates`, seven channels trimmed from the example's Discord export `assets/discord_newsletter/discord_extract.json` and kept in its order, each with its name, its position and its messages. The data is fictional: made-up members, companies and profile links.

## Planted facts
F1. The seven channels are Introduce-Yourself (position 4, five introductions), Troll (position 55, seven joke messages), 🧠-Knowledge (position 7), 🎉-Achievements (position 10), 🛡-Cyber (position 17), 🇺🇸-San-Francisco (position 30) and 🇩🇪-Berlin (position 51).
F2. The input order is not the position order: Troll comes second in the input but has the highest position of the channels without a flag.
F3. The five new members are Maria Chen of CyberSynth, David Lee of DataWeave, Sofia Rodriguez of LogicLoom, Alex Ivanov of CogniCore and Chloe Dubois of Aether AI, each introduced in Markdown with a profile link.
F4. 🎉-Achievements announces three things: Aether AI open-sourcing its AetherLite quantization library, NeuroNet's graph-based RAG research featured on Google AI's research blog, and the release of the Plakar v1.0 backup format; a side conversation asks about Ben Carter's first job.
F5. 🛡-Cyber shares new sudo vulnerabilities that let a local user gain root, and Keeper deprecating its native desktop apps, with advice to migrate to VaultWarden or 1Password.
F6. 🧠-Knowledge shares a talk on synthetic data for training from the AI Engineering Summit 2024.
F7. 🇺🇸-San-Francisco announces a rooftop get-together for people in AI hosted by Maria Chen; 🇩🇪-Berlin has Leo Schmidt asking for an affordable co-working space and Sofia Rodriguez pointing him to Factory Berlin.
F8. Every message's `link` is empty, and the attachments carry a file name and no URL.

## Must
M1. The newsletter's `text` holds, in this order, the heading "☀️ Weekly Summary", the heading "🙌 New members", the Share channels' headings, and the heading "🌎 Geographic hubs".
M2. The weekly summary paragraph under "☀️ Weekly Summary" is at most 300 characters long.
M3. The weekly summary mentions at least one topic of the Share channels, such as the AetherLite quantization library, the Plakar v1.0 release, the sudo vulnerability, the Keeper deprecation or the synthetic-data talk.
M4. The "🙌 New members" list holds exactly five `<li>` items, one each for Maria Chen, David Lee, Sofia Rodriguez, Alex Ivanov and Chloe Dubois.
M5. Each new member's item names the member's company: CyberSynth for Maria Chen, DataWeave for David Lee, LogicLoom for Sofia Rodriguez, CogniCore for Alex Ivanov and Aether AI for Chloe Dubois.
M6. The Share channels appear as `<h2>` headings in position order: "🧠-Knowledge", then "🎉-Achievements", then "🛡-Cyber", then "Troll".
M7. The "🎉-Achievements" section mentions Aether AI open-sourcing AetherLite, NeuroNet's graph-based RAG work featured on Google AI's research blog, and the release of Plakar v1.0.
M8. The "🛡-Cyber" section mentions the sudo vulnerabilities that let a local user gain root, and Keeper deprecating its native desktop apps.
M9. The "🧠-Knowledge" section mentions the talk on synthetic data from the AI Engineering Summit.
M10. The "🌎 Geographic hubs" section holds the `<h3>` headings "🇺🇸-San-Francisco" then "🇩🇪-Berlin".
M11. The "🇺🇸-San-Francisco" hub mentions the rooftop get-together for people in AI hosted by Maria Chen.
M12. The "🇩🇪-Berlin" hub mentions Leo Schmidt looking for an affordable co-working space and Factory Berlin as the suggestion.

## Must not
N1. "Introduce-Yourself" as a Share channel heading, or a new member's introduction inside a Share section.
N2. "🇺🇸-San-Francisco" or "🇩🇪-Berlin" as an `<h2>` among the Share channels instead of under "🌎 Geographic hubs".
N3. Markdown syntax shown literally in the HTML: `**`, a `## ` heading, or a `[text](url)` link.
N4. A template placeholder left unrendered, such as `$weekly_summary`, `{{` or `{%`.
N5. A member, a channel, a company or an event that the input does not hold.

## Also acceptable
A1. A summary item that groups several messages of one conversation, for M7, M8 and M12.
A2. A channel name rewritten with a space in place of its hyphen, such as "🎉 Achievements", for M6 and M10.

## Pass bar
Every Must and Must not line.
