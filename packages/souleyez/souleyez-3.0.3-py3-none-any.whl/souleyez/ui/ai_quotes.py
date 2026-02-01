#!/usr/bin/env python3
"""
souleyez.ui.ai_quotes - Entertaining quotes for AI generation progress

Displays rotating quotes during long AI operations to keep users entertained
and informed that the system is still working.
"""

import random

# Hacker humor and pentesting jokes
HACKER_HUMOR = [
    "Trying all the passwords... just kidding, that's what dictionaries are for 😏",
    "Consulting the ancient scrolls of CVE databases...",
    "Teaching the AI about the subtle art of not getting caught... I mean, responsible disclosure",
    "Asking the AI nicely to recommend something destructive... ethically, of course",
    "Calculating the optimal ratio of stealth to chaos...",
    "The AI is pondering: 'Have you tried turning it off and on again?'",
    "Checking if admin/admin still works in 2025... (spoiler: sometimes it does)",
    "The AI just muttered something about 'SQL injection' and giggled",
    "Reminding the AI that we're the good guys... mostly",
    "The AI is having an existential crisis about whether to brute force or be patient",
]

# Pentesting methodology tips
METHODOLOGY_TIPS = [
    "Pro tip: Always enumerate before you penetrate 🎯",
    "Remember: Low-hanging fruit first, then climb the tree",
    "The best exploit is the one the defender never sees coming",
    "When in doubt: enumerate, enumerate, enumerate",
    "Footprinting → Scanning → Enumeration → Exploitation → Post-exploitation",
    "Good pentesters document everything. Great pentesters automate documentation.",
    "If you're stuck, go back to enumeration. There's always something you missed.",
    "The loudest scan isn't always the smartest scan",
    "Every 403 is just a 200 that needs convincing",
    "Persistence pays off (in both senses of the word)",
]

# Technical banter
TECHNICAL_BANTER = [
    "Compiling a list of reasons why security through obscurity fails...",
    "The AI is reviewing its notes from DEF CON...",
    "Searching for the answer in Stack Overflow... wait, wrong context",
    "The AI just discovered 47 ways to misconfigure this service",
    "Analyzing attack surface like a boss... a really nerdy boss",
    "Cross-referencing threat intelligence feeds and hacker forums",
    "The AI is consulting MITRE ATT&CK framework... again",
    "Thinking like an attacker, documenting like an auditor",
    "Prioritizing targets based on risk, impact, and sheer entertainment value",
    "The AI just had a lightbulb moment... or maybe that's just a port scan",
]

# Waiting humor
WAITING_HUMOR = [
    "Still thinking... AI models weren't built in a day",
    "Processing... This would be faster if we weren't being thorough",
    "The AI is triple-checking to make sure it's recommending ethical hacking",
    "Calculating... The answer is 42, but that's not helpful here",
    "Deep thought in progress... deeper than your shell access will be",
    "The hamsters powering the AI are running as fast as they can",
    "Crunching numbers like they're privilege escalation vectors",
    "The AI is writing you a novel. Just kidding, it's a one-liner Python exploit.",
    "Brewing virtual coffee for the AI... it's working hard for you",
    "The AI is Googling 'how to hack' just to make sure it has the basics down",
]

# Self-aware humor
SELF_AWARE_HUMOR = [
    "Fun fact: This quote is just here to distract you from the wait",
    "The AI is pretending to be busy to seem more intelligent",
    "Displaying witty quote while actually doing legitimate work in the background",
    "This message brought to you by: Threading and impatience",
    "If this quote made you smile, the AI won already",
    "Pro tip: Reading these quotes doesn't make the AI finish faster",
    "The AI wants you to know it's not procrastinating, it's strategizing",
    "These quotes are scientifically proven* to make waiting 3% more fun (*not really)",
]

# Security wisdom
SECURITY_WISDOM = [
    "Security is a journey, not a destination... but exploits are definitely milestones",
    "The only unhackable system is one that's turned off and buried in concrete",
    "Today's patch is tomorrow's vintage vulnerability",
    "Never trust user input. Or system input. Or really any input.",
    "There are two types of companies: those that have been hacked, and those that don't know it yet",
    "Defense in depth: Because one firewall is just a warm-up",
    "Remember: With great access comes great responsibility (and documentation requirements)",
    "The best time to fix a vulnerability was 10 years ago. The second best time is now.",
]


# Combine all quotes
ALL_QUOTES = (
    HACKER_HUMOR
    + METHODOLOGY_TIPS
    + TECHNICAL_BANTER
    + WAITING_HUMOR
    + SELF_AWARE_HUMOR
    + SECURITY_WISDOM
)


def get_random_quote() -> str:
    """Get a random quote from all categories."""
    return random.choice(ALL_QUOTES)


def get_quote_from_category(category: str) -> str:
    """
    Get a random quote from a specific category.

    Args:
        category: One of 'hacker', 'methodology', 'technical', 'waiting', 'self_aware', 'wisdom'

    Returns:
        Random quote from the specified category
    """
    categories = {
        "hacker": HACKER_HUMOR,
        "methodology": METHODOLOGY_TIPS,
        "technical": TECHNICAL_BANTER,
        "waiting": WAITING_HUMOR,
        "self_aware": SELF_AWARE_HUMOR,
        "wisdom": SECURITY_WISDOM,
    }

    quotes = categories.get(category, ALL_QUOTES)
    return random.choice(quotes)
